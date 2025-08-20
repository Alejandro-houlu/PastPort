import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

  userData: any = null;
  currentTime = new Date();

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.loadUserData();
    
    // Update time every minute
    setInterval(() => {
      this.currentTime = new Date();
    }, 60000);
  }

  /**
   * Load user data
   */
  private loadUserData(): void {
    // Try to get user data from localStorage
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
   * Open camera for face recognition
   */
  openCamera(): void {
    // Navigate to face recognition component
    this.router.navigate(['/auth/face-login']);
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
