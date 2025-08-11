import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'auth/login',
    loadComponent: () => import('./Components/AuthComponents/login/login').then(m => m.Login)
  },
  {
    path: '',
    redirectTo: '/auth/login',
    pathMatch: 'full'
  }
];
