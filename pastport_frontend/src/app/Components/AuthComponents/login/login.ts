import { Component, OnInit } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class Login implements OnInit {
  year: number = new Date().getFullYear();
  isHovering = false;

  constructor(private router: Router) {}

  ngOnInit(): void {
    // Component initialization if needed
    console.log('Landing component initialized');
  }

  /**
   * Navigate to face login page
   */
  onFaceLogin(): void {
    this.router.navigate(['/auth/face-login']);
  }

  /**
   * Set hover state for button animation
   * @param state - hover state (true/false)
   */
  setHovering(state: boolean): void {
    this.isHovering = state;
  }

  /**
   * Navigate to registration page
   */
  onRegister(): void {
    this.router.navigate(['/auth/register']);
  }
}