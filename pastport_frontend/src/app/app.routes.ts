import { Routes } from '@angular/router';
import { AuthGuard } from './Services/auth.guard';

export const routes: Routes = [
  // Authentication routes (no layout)
  {
    path: 'auth/login',
    loadComponent: () => import('./Components/AuthComponents/login/login').then(m => m.Login)
  },
  {
    path: 'auth/face-login',
    loadComponent: () => import('./Components/AuthComponents/face_login/face_login.component').then(m => m.FaceLoginComponent)
  },
  
  // Main application routes (with layout)
  {
    path: '',
    loadComponent: () => import('./Components/Layouts/layout.component').then(m => m.LayoutComponent),
    // canActivate: [AuthGuard], // Temporarily disabled for development
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./Components/Dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'travel-history',
        loadComponent: () => import('./Components/Dashboard/dashboard.component').then(m => m.DashboardComponent) // Placeholder
      },
      {
        path: 'documents',
        loadComponent: () => import('./Components/Dashboard/dashboard.component').then(m => m.DashboardComponent) // Placeholder
      },
      {
        path: 'face-recognition',
        loadComponent: () => import('./Components/Dashboard/dashboard.component').then(m => m.DashboardComponent) // Placeholder
      },
      {
        path: 'profile',
        loadComponent: () => import('./Components/Dashboard/dashboard.component').then(m => m.DashboardComponent) // Placeholder
      },
      {
        path: 'settings',
        loadComponent: () => import('./Components/Dashboard/dashboard.component').then(m => m.DashboardComponent) // Placeholder
      },
      {
        path: '',
        redirectTo: '/dashboard',
        pathMatch: 'full'
      }
    ]
  },
  
  // Fallback route
  {
    path: '**',
    redirectTo: '/auth/login'
  }
];
