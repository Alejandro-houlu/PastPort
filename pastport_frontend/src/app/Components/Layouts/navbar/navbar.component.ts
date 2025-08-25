import { Component, OnInit, OnDestroy, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { Subscription } from 'rxjs';
import { AuthService, User } from '../../../Services/auth.service';
import { UserDataService, UserDataLoadingState } from '../../../Services/user-data.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, NgbDropdownModule],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent implements OnInit, OnDestroy {

  @Output() mobileMenuButtonClicked = new EventEmitter();

  userData: User | null = null;
  isLoadingUserData = false;
  
  private userDataSubscription?: Subscription;

  constructor(
    private router: Router,
    private authService: AuthService,
    private userDataService: UserDataService
  ) {}

  ngOnInit(): void {
    this.loadUserData();
  }

  ngOnDestroy(): void {
    if (this.userDataSubscription) {
      this.userDataSubscription.unsubscribe();
    }
  }

  /**
   * Load user data using UserDataService (cached only, no backend verification)
   */
  private async loadUserData(): Promise<void> {
    try {
      const result = await this.userDataService.loadUserDataCached();
      
      this.isLoadingUserData = result.isLoading;
      this.userData = result.userData;
      
      // Subscribe to loading state changes
      this.userDataSubscription = this.userDataService.loadingState$.subscribe(state => {
        this.isLoadingUserData = state.isLoading;
        this.userData = state.userData;
      });
      
    } catch (error) {
      console.error('Error loading user data in navbar:', error);
      this.userData = null;
      this.isLoadingUserData = false;
    }
  }

  /**
   * Toggle mobile menu
   */
  toggleMobileMenu(): void {
    // Add hamburger animation (following TravelDx pattern)
    document.querySelector('.hamburger-icon')?.classList.toggle('open');
    this.mobileMenuButtonClicked.emit();
  }

  /**
   * Logout user
   */
  logout(): void {
    this.authService.logout();
    this.router.navigate(['/auth/login']);
  }

  /**
   * Navigate to profile
   */
  goToProfile(): void {
    // Future implementation
    console.log('Navigate to profile');
  }

  /**
   * Navigate to settings
   */
  goToSettings(): void {
    // Future implementation
    console.log('Navigate to settings');
  }
}
