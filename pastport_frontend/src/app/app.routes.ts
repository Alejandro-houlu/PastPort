import { Routes } from '@angular/router';
import { AuthGuard } from './Services/auth.guard';
import { MainCamComponent } from './Components/mainCam/main-cam.component';

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
  
  // Camera route (no layout - full screen)
  {
    path: 'camera',
    loadComponent: () => import('./Components/mainCam/main-cam.component').then(m => m.MainCamComponent),
    canActivate:[AuthGuard]
  },
  
  // Main application routes (with layout)
  {
    path: '',
    loadComponent: () => import('./Components/Layouts/layout.component').then(m => m.LayoutComponent),
    canActivate: [AuthGuard],

    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./Components/Dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'artifact/:id',
        loadComponent: () => import('./Components/Artifact/artifact-display.component').then(m => m.ArtifactDisplayComponent)
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
        redirectTo: '/auth/login',
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
