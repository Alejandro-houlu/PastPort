import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { AuthService, User } from './auth.service';
import { UserVerificationResult } from '../Models/user.models';

export interface UserDataLoadingState {
  isLoading: boolean;
  userData: User | null;
  error: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class UserDataService {
  private loadingStateSubject = new BehaviorSubject<UserDataLoadingState>({
    isLoading: false,
    userData: null,
    error: null
  });

  public loadingState$ = this.loadingStateSubject.asObservable();

  constructor(private authService: AuthService) {
    // Subscribe to auth service user changes
    this.authService.currentUser$.subscribe(user => {
      this.updateLoadingState({
        isLoading: false,
        userData: user,
        error: null
      });
    });
  }

  /**
   * Load user data with optional backend verification (for dashboard)
   */
  async loadUserDataWithVerification(): Promise<UserDataLoadingState> {
    this.updateLoadingState({
      isLoading: true,
      userData: this.authService.getCurrentUser(),
      error: null
    });

    try {
      // First get cached user data
      const cachedUser = this.authService.getCurrentUser();
      
      if (!cachedUser) {
        // No user data found
        const finalState = {
          isLoading: false,
          userData: null,
          error: 'No user data found'
        };
        this.updateLoadingState(finalState);
        return finalState;
      }

      // Set cached data immediately for better UX
      this.updateLoadingState({
        isLoading: true,
        userData: cachedUser,
        error: null
      });

      // Verify with backend
      const verificationResult: UserVerificationResult = await this.authService.verifyCurrentUser();
      
      if (verificationResult.isValid) {
        // Update with verified data (may have been updated during verification)
        const finalState = {
          isLoading: false,
          userData: this.authService.getCurrentUser(),
          error: null
        };
        this.updateLoadingState(finalState);
        
        if (verificationResult.discrepancies.length > 0) {
          console.log('User data was updated from backend:', verificationResult.discrepancies);
        }
        
        return finalState;
      } else {
        // Verification failed
        const error = verificationResult.error || 'Failed to verify user data';
        
        if (verificationResult.error === 'Authentication failed' || 
            verificationResult.error === 'User not found' ||
            verificationResult.error === 'User ID verification failed') {
          // Critical errors - clear user data
          const finalState = {
            isLoading: false,
            userData: null,
            error: error
          };
          this.updateLoadingState(finalState);
          return finalState;
        }
        
        // For network errors, continue with cached data but show warning
        console.warn('Using cached user data due to verification error:', verificationResult.error);
        const finalState = {
          isLoading: false,
          userData: cachedUser,
          error: `Warning: ${error}`
        };
        this.updateLoadingState(finalState);
        return finalState;
      }
    } catch (error) {
      console.error('Error loading user data:', error);
      const errorMessage = 'Failed to load user data';
      
      // If we have cached data, use it as fallback
      const cachedUser = this.authService.getCurrentUser();
      const finalState = {
        isLoading: false,
        userData: cachedUser,
        error: cachedUser ? `Warning: ${errorMessage}` : errorMessage
      };
      this.updateLoadingState(finalState);
      return finalState;
    }
  }

  /**
   * Load user data without backend verification (for navbar and other components)
   */
  async loadUserDataCached(): Promise<UserDataLoadingState> {
    this.updateLoadingState({
      isLoading: true,
      userData: this.authService.getCurrentUser(),
      error: null
    });

    try {
      // Get cached user data from AuthService
      const cachedUser = this.authService.getCurrentUser();
      
      const finalState = {
        isLoading: false,
        userData: cachedUser,
        error: cachedUser ? null : 'No user data found'
      };
      
      this.updateLoadingState(finalState);
      return finalState;
    } catch (error) {
      console.error('Error loading cached user data:', error);
      const finalState = {
        isLoading: false,
        userData: null,
        error: 'Failed to load user data'
      };
      this.updateLoadingState(finalState);
      return finalState;
    }
  }

  /**
   * Get current loading state
   */
  getCurrentState(): UserDataLoadingState {
    return this.loadingStateSubject.value;
  }

  /**
   * Get current user data (shortcut)
   */
  getCurrentUser(): User | null {
    return this.authService.getCurrentUser();
  }

  /**
   * Check if currently loading
   */
  isLoading(): boolean {
    return this.loadingStateSubject.value.isLoading;
  }

  /**
   * Update loading state and notify subscribers
   */
  private updateLoadingState(state: UserDataLoadingState): void {
    this.loadingStateSubject.next(state);
  }

  /**
   * Reset loading state
   */
  resetState(): void {
    this.updateLoadingState({
      isLoading: false,
      userData: this.authService.getCurrentUser(),
      error: null
    });
  }
}
