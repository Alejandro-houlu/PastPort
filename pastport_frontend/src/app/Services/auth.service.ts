import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { 
  AuthenticationResponse, 
  FaceLoginRequest, 
  RegistrationRequest 
} from '../Models/face-recognition.models';

export interface User {
  id: string;
  name: string;
  age_group: 'child' | 'teen' | 'adult' | 'senior';
  email?: string;
}

export interface JWTPayload {
  sub: string; // user id
  name: string;
  age_group: 'child' | 'teen' | 'adult' | 'senior';
  exp: number; // expiration timestamp
  iat: number; // issued at timestamp
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly API_BASE_URL = 'http://localhost:8000/api/v1'; // Backend URL
  private readonly TOKEN_KEY = 'pastport_jwt_token';
  private readonly USER_KEY = 'pastport_user_data';

  private currentUserSubject = new BehaviorSubject<User | null>(this.loadUserFromStorage());
  public currentUser$ = this.currentUserSubject.asObservable();

  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasValidToken());
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  constructor(private http: HttpClient) {
    // Check token expiration on service initialization
    this.checkTokenExpiration();
  }

  /**
   * Perform facial recognition login
   */
  faceLogin(faceImage: string, deviceInfo?: string): Observable<AuthenticationResponse> {
    const request: FaceLoginRequest = {
      face_image: faceImage,
      device_info: deviceInfo
    };

    return this.http.post<AuthenticationResponse>(`${this.API_BASE_URL}/auth/face-login`, request)
      .pipe(
        tap(response => {
          if (response.status === 'success' && response.action === 'login') {
            this.handleSuccessfulLogin(response);
          }
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Complete user registration after face capture
   */
  completeRegistration(tempFaceId: string, username: string): Observable<AuthenticationResponse> {
    const request: RegistrationRequest = {
      temp_face_id: tempFaceId,
      username: username
    };

    return this.http.post<AuthenticationResponse>(`${this.API_BASE_URL}/auth/complete-registration`, request)
      .pipe(
        tap(response => {
          if (response.status === 'success' && response.action === 'login') {
            this.handleSuccessfulLogin(response);
          }
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Handle successful login response with JWT token
   */
  private handleSuccessfulLogin(response: AuthenticationResponse): void {
    if (response.token && response.user) {
      // Store JWT token
      localStorage.setItem(this.TOKEN_KEY, response.token);
      
      // Decode JWT to get user data (for validation)
      const decodedToken = this.decodeJWT(response.token);
      
      // Store user data
      const user: User = {
        id: response.user.id,
        name: response.user.name,
        age_group: response.user.age_group
      };
      
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      
      // Update subjects
      this.currentUserSubject.next(user);
      this.isAuthenticatedSubject.next(true);
      
      // Set up token expiration check
      this.scheduleTokenExpirationCheck(decodedToken?.exp);
    }
  }

  /**
   * Decode JWT token (client-side for expiration checking)
   */
  private decodeJWT(token: string): JWTPayload | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Error decoding JWT:', error);
      return null;
    }
  }

  /**
   * Check if JWT token is expired
   */
  private isTokenExpired(token: string): boolean {
    const decoded = this.decodeJWT(token);
    if (!decoded) return true;
    
    const currentTime = Math.floor(Date.now() / 1000);
    return decoded.exp < currentTime;
  }

  /**
   * Schedule token expiration check
   */
  private scheduleTokenExpirationCheck(exp?: number): void {
    if (!exp) return;
    
    const currentTime = Math.floor(Date.now() / 1000);
    const timeUntilExpiration = (exp - currentTime) * 1000; // Convert to milliseconds
    
    if (timeUntilExpiration > 0) {
      setTimeout(() => {
        this.handleTokenExpiration();
      }, timeUntilExpiration);
    }
  }

  /**
   * Handle token expiration
   */
  private handleTokenExpiration(): void {
    console.log('JWT token expired, logging out user');
    this.logout();
  }

  /**
   * Check token expiration on app load
   */
  private checkTokenExpiration(): void {
    const token = this.getToken();
    if (token && this.isTokenExpired(token)) {
      this.logout();
    }
  }

  /**
   * Logout user and clear JWT token
   */
  logout(): void {
    // Clear stored data
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    
    // Update subjects
    this.currentUserSubject.next(null);
    this.isAuthenticatedSubject.next(false);
  }

  /**
   * Get current user
   */
  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Check if user is authenticated with valid JWT
   */
  isAuthenticated(): boolean {
    return this.isAuthenticatedSubject.value;
  }

  /**
   * Get JWT token
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Get HTTP headers with JWT Bearer token
   */
  getAuthHeaders(): HttpHeaders {
    const token = this.getToken();
    return new HttpHeaders({
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    });
  }

  /**
   * Check if stored JWT token is valid
   */
  private hasValidToken(): boolean {
    const token = this.getToken();
    const user = this.loadUserFromStorage();
    
    if (!token || !user) return false;
    
    // Check if token is expired
    return !this.isTokenExpired(token);
  }

  /**
   * Load user data from localStorage
   */
  private loadUserFromStorage(): User | null {
    try {
      const stored = localStorage.getItem(this.USER_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      console.error('Error loading user from storage:', error);
      return null;
    }
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: any): Observable<never> {
    console.error('Auth service error:', error);
    
    // Handle JWT-specific errors
    if (error.status === 401) {
      // Unauthorized - token might be expired or invalid
      this.logout();
    }
    
    let errorMessage = 'An error occurred during authentication';
    
    if (error.error?.message) {
      errorMessage = error.error.message;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    return throwError(() => new Error(errorMessage));
  }

  /**
   * Refresh authentication state (useful for app initialization)
   */
  refreshAuthState(): void {
    const user = this.loadUserFromStorage();
    const hasToken = this.hasValidToken();
    
    this.currentUserSubject.next(user);
    this.isAuthenticatedSubject.next(hasToken);
  }

  /**
   * Get user's age group for chatbot tone
   */
  getUserAgeGroup(): 'child' | 'teen' | 'adult' | 'senior' | null {
    const user = this.getCurrentUser();
    return user ? user.age_group : null;
  }

  /**
   * Get JWT token payload
   */
  getTokenPayload(): JWTPayload | null {
    const token = this.getToken();
    return token ? this.decodeJWT(token) : null;
  }

  /**
   * Check if token will expire soon (within 5 minutes)
   */
  isTokenExpiringSoon(): boolean {
    const payload = this.getTokenPayload();
    if (!payload) return false;
    
    const currentTime = Math.floor(Date.now() / 1000);
    const fiveMinutes = 5 * 60; // 5 minutes in seconds
    
    return (payload.exp - currentTime) < fiveMinutes;
  }

  /**
   * Clear all authentication data (for testing/reset)
   */
  clearAllAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem('pastport_face_embeddings');
    localStorage.removeItem('pastport_biometric_consent');
    
    this.currentUserSubject.next(null);
    this.isAuthenticatedSubject.next(false);
  }
}
