import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../../Services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent implements OnInit {

  @Output() mobileMenuButtonClicked = new EventEmitter();

  userData: any = null;

  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Get user data from auth service or local storage
    this.loadUserData();
  }

  /**
   * Load user data
   */
  private loadUserData(): void {
    // Try to get user data from auth service or localStorage
    const token = localStorage.getItem('pastport_jwt_token');
    if (token) {
      // For now, we'll use a simple approach
      // In a real app, you'd decode the JWT or call an API
      this.userData = {
        username: 'User', // This would come from JWT or API
        email: 'user@pastport.com'
      };
    }
  }

  /**
   * Toggle mobile menu
   */
  toggleMobileMenu(): void {
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
