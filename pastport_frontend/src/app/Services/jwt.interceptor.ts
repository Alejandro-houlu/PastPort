import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';

/**
 * Functional HTTP interceptor for adding JWT token to requests
 * This is the modern Angular approach for interceptors
 */
export const jwtInterceptorFn: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  
  // Helper function to check if URL is an auth endpoint
  const isAuthUrl = (url: string): boolean => {
    return url.includes('/auth/login') || 
           url.includes('/auth/register') || 
           url.includes('/auth/face-login') || 
           url.includes('/auth/face-register') ||
           url.includes('/auth/refresh');
  };
  
  // Get token from auth service
  const token = authService.getToken();
  
  // DEBUG LOGGING
  console.log('🔐 JWT Interceptor - Request:', {
    method: req.method,
    url: req.url,
    hasToken: !!token,
    tokenPreview: token ? token.substring(0, 20) + '...' : 'NO TOKEN',
    isAuthUrl: isAuthUrl(req.url),
    willAddAuth: !!(token && !isAuthUrl(req.url))
  });
  
  // Clone request and add authorization header if token exists and not an auth URL
  let authReq = req;
  if (token && !isAuthUrl(req.url)) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    console.log('✅ Added Authorization header');
  } else {
    console.warn('⚠️ Authorization header NOT added:', {
      hasToken: !!token,
      isAuthUrl: isAuthUrl(req.url)
    });
  }
  
  // Handle the request and catch errors
  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle 401 errors (token expired/invalid)
      if (error.status === 401 && !isAuthUrl(req.url)) {
        console.warn('JWT token expired or invalid, logging out user');
        authService.logout();
        return throwError(() => new Error('Session expired. Please login again.'));
      }
      
      return throwError(() => error);
    })
  );
};
