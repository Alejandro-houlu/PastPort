import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class Login implements OnInit {
  loginForm!: FormGroup;
  submitted = false;
  fieldTextType = false;
  error = '';
  year: number = new Date().getFullYear();

  constructor(
    private formBuilder: FormBuilder,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Initialize the login form
    this.loginForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]]
    });
  }

  // Convenience getter for easy access to form fields
  get f() { 
    return this.loginForm.controls; 
  }

  /**
   * Form submit
   */
  onSubmit() {
    this.submitted = true;

    // Stop here if form is invalid
    if (this.loginForm.invalid) {
      return;
    }

    // TODO: Implement actual authentication with Django backend
    console.log('Login attempt:', {
      email: this.f['email'].value,
      password: this.f['password'].value
    });

    // For now, just log the attempt (will connect to Django backend later)
    alert('Login functionality will be connected to Django backend');
  }

  /**
   * Toggle password visibility
   */
  toggleFieldTextType() {
    this.fieldTextType = !this.fieldTextType;
  }
}
