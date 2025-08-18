import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'auth/login',
    loadComponent: () => import('./Components/AuthComponents/login/login').then(m => m.Login)
  },
  {
    path: 'auth/face-login',
    loadComponent: () => import('./Components/AuthComponents/face_login/face_login.component').then(m => m.FaceLoginComponent)
  },
  {
    path: '',
    redirectTo: '/auth/login',
    pathMatch: 'full'
  }
];
