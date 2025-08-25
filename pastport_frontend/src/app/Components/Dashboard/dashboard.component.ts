import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { AuthService, User } from '../../Services/auth.service';
import { UserDataService, UserDataLoadingState } from '../../Services/user-data.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {

  userData: User | null = null;
  currentTime = new Date();
  isLoadingUserData = false;
  verificationError: string | null = null;
  
  private userDataSubscription?: Subscription;

  constructor(
    private router: Router,
    private authService: AuthService,
    private userDataService: UserDataService
  ) {}

  ngOnInit(): void {
    this.loadUserData();
    
    // Update time every minute
    setInterval(() => {
      this.currentTime = new Date();
    }, 60000);
  }

  ngOnDestroy(): void {
    if (this.userDataSubscription) {
      this.userDataSubscription.unsubscribe();
    }
  }

  /**
   * Load user data with backend verification using UserDataService
   */
  private async loadUserData(): Promise<void> {
    try {
      const result = await this.userDataService.loadUserDataWithVerification();
      
      this.isLoadingUserData = result.isLoading;
      this.userData = result.userData;
      this.verificationError = result.error;
      
      // Handle critical errors that require redirect to login
      if (!result.userData && result.error && 
          (result.error.includes('Authentication failed') || 
           result.error.includes('User not found') ||
           result.error.includes('User ID verification failed') ||
           result.error === 'No user data found')) {
        this.router.navigate(['/auth/login']);
        return;
      }
      
      // Subscribe to loading state changes
      this.userDataSubscription = this.userDataService.loadingState$.subscribe(state => {
        this.isLoadingUserData = state.isLoading;
        this.userData = state.userData;
        this.verificationError = state.error;
      });
      
    } catch (error) {
      console.error('Error loading user data:', error);
      this.verificationError = 'Failed to load user data';
      this.isLoadingUserData = false;
      
      if (!this.userData) {
        this.router.navigate(['/auth/login']);
      }
    }
  }

  /**
   * Open camera for face recognition
   */
  openCamera(): void {
    // Navigate to face recognition component
    this.router.navigate(['/camera']);
  }

  /**
   * Get greeting based on time of day
   */
  getGreeting(): string {
    const hour = this.currentTime.getHours();
    
    if (hour < 12) {
      return 'Good Morning';
    } else if (hour < 17) {
      return 'Good Afternoon';
    } else {
      return 'Good Evening';
    }
  }

  /**
   * Get formatted date
   */
  getFormattedDate(): string {
    return this.currentTime.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  /**
   * Get formatted time
   */
  getFormattedTime(): string {
    return this.currentTime.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}
