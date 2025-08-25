import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, firstValueFrom } from 'rxjs';
import { 
  AuthenticationResponse, 
  FaceLoginRequest, 
  RegistrationRequest 
} from '../Models/face-recognition.models';
import { 
  BackendUserResponse, 
  UserVerificationResult, 
  UserComparisonResult 
} from '../Models/user.models';
import { environment } from '../../environments/environment';

export interface EmailLoginRequest {
  email: string;
  password: string;
}

export interface EmailRegistrationRequest {
  email: string;
  password: string;
  name: string;
  age_group: 'child' | 'teen' | 'adult' | 'senior';
}

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
  private readonly API_BASE_URL = `${environment.apiUrl}`; // Backend URL
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
   * Perform email/password login
   */
  async emailLogin(email: string, password: string): Promise<AuthenticationResponse> {
    const request: EmailLoginRequest = {
      email: email,
      password: password
    };

    try {
      const response = await firstValueFrom(
        this.http.post<AuthenticationResponse>(`${this.API_BASE_URL}/auth/email-login`, request)
      );
      
      if (response.status === 'success' && response.action === 'login') {
        this.handleSuccessfulLogin(response);
      }
      
      return response;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Register new user with email/password
   */
  async emailRegister(email: string, password: string, name: string, age_group: 'child' | 'teen' | 'adult' | 'senior'): Promise<AuthenticationResponse> {
    const request: EmailRegistrationRequest = {
      email: email,
      password: password,
      name: name,
      age_group: age_group
    };

    try {
      const response = await firstValueFrom(
        this.http.post<AuthenticationResponse>(`${this.API_BASE_URL}/auth/email-register`, request)
      );
      
      if (response.status === 'success' && response.action === 'login') {
        this.handleSuccessfulLogin(response);
      }
      
      return response;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Perform facial recognition login
   */
  async faceLogin(embeddings: number[][], deviceInfo?: string): Promise<AuthenticationResponse> {
    const request: FaceLoginRequest = {
      embeddings: embeddings,
      device_info: deviceInfo
    };

    try {
      const response = await firstValueFrom(
        this.http.post<AuthenticationResponse>(`${this.API_BASE_URL}/auth/face-login`, request)
      );
      
      if (response.status === 'success' && response.action === 'login') {
        this.handleSuccessfulLogin(response);
      }
      
      return response;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Complete user registration after face capture
   */
  async completeRegistration(tempFaceId: string, username: string): Promise<AuthenticationResponse> {
    const request: RegistrationRequest = {
      temp_face_id: tempFaceId,
      username: username
    };

    try {
      const response = await firstValueFrom(
        this.http.post<AuthenticationResponse>(`${this.API_BASE_URL}/auth/complete-registration`, request)
      );
      
      if (response.status === 'success' && response.action === 'login') {
        this.handleSuccessfulLogin(response);
      }
      
      return response;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Handle successful login response with JWT token
   */
  public handleSuccessfulLogin(response: AuthenticationResponse): void {
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
  private handleError(error: any): Error {
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
    
    return new Error(errorMessage);
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
   * Verify current user with backend API
   */
  async verifyCurrentUser(): Promise<UserVerificationResult> {
    const token = this.getToken();
    const localUser = this.getCurrentUser();

    if (!token || !localUser) {
      return {
        isValid: false,
        userData: null,
        discrepancies: ['No token or user data found in localStorage'],
        error: 'User not authenticated'
      };
    }

    try {
      const response = await firstValueFrom(
        this.http.get<BackendUserResponse>(`${this.API_BASE_URL}/auth/me`, {
          headers: this.getAuthHeaders()
        })
      );

      // Compare user ID only (as requested)
      const userIdMatches = localUser.id === response.user_id;
      
      if (userIdMatches) {
        // Update localStorage with latest backend data
        this.updateUserDataFromBackend(response);
        
        return {
          isValid: true,
          userData: response,
          discrepancies: []
        };
      } else {
        // User ID mismatch - this is a serious issue, logout user
        this.logout();
        return {
          isValid: false,
          userData: null,
          discrepancies: [`User ID mismatch: localStorage(${localUser.id}) != backend(${response.user_id})`],
          error: 'User ID verification failed'
        };
      }
    } catch (error: any) {
      console.error('Error verifying user with backend:', error);
      
      // Handle specific error cases
      if (error.status === 401) {
        // Token is invalid, logout user
        this.logout();
        return {
          isValid: false,
          userData: null,
          discrepancies: ['Invalid or expired token'],
          error: 'Authentication failed'
        };
      } else if (error.status === 404) {
        // User not found in backend
        this.logout();
        return {
          isValid: false,
          userData: null,
          discrepancies: ['User not found in backend'],
          error: 'User not found'
        };
      } else {
        // Network or other errors - return cached data but flag the error
        return {
          isValid: false,
          userData: null,
          discrepancies: ['Network error or server unavailable'],
          error: error.message || 'Failed to verify user with backend'
        };
      }
    }
  }

  /**
   * Update localStorage user data with backend data
   */
  private updateUserDataFromBackend(backendUser: BackendUserResponse): void {
    const updatedUser: User = {
      id: backendUser.user_id,
      name: backendUser.username,
      age_group: (backendUser.age_group as 'child' | 'teen' | 'adult' | 'senior') || 'adult',
      email: backendUser.email
    };

    // Update localStorage
    localStorage.setItem(this.USER_KEY, JSON.stringify(updatedUser));
    
    // Update BehaviorSubject
    this.currentUserSubject.next(updatedUser);
    
    console.log('Updated localStorage user data with backend data:', updatedUser);
  }

  /**
   * Get current user with optional backend verification
   */
  async getCurrentUserVerified(verifyWithBackend: boolean = false): Promise<User | null> {
    if (!verifyWithBackend) {
      return this.getCurrentUser();
    }

    try {
      const verificationResult = await this.verifyCurrentUser();
      
      if (verificationResult.isValid && verificationResult.userData) {
        // Return the current user (which may have been updated during verification)
        return this.getCurrentUser();
      } else {
        // Verification failed, return null
        return null;
      }
    } catch (error) {
      console.error('Error during user verification:', error);
      // Return cached user data as fallback
      return this.getCurrentUser();
    }
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
