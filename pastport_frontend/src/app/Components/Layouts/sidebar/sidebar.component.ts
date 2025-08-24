import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, NavigationEnd } from '@angular/router';
import { RouterModule } from '@angular/router';

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  link?: string;
  isActive?: boolean;
  subItems?: MenuItem[];
  isCollapsed?: boolean;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit {

  menuItems: MenuItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: 'bx bx-home-circle',
      link: '/dashboard',
      isActive: true
    },
    {
      id: 'travel-history',
      label: 'Travel History',
      icon: 'bx bx-map',
      link: '/travel-history'
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: 'bx bx-file',
      link: '/documents'
    },
    {
      id: 'face-recognition',
      label: 'Face Recognition',
      icon: 'bx bx-face',
      link: '/face-recognition'
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: 'bx bx-user',
      link: '/profile'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: 'bx bx-cog',
      link: '/settings'
    }
  ];

  constructor(private router: Router) {}

  ngOnInit(): void {
    // Listen to route changes to update active menu item
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        this.updateActiveMenuItem(event.url);
      }
    });

    // Set initial active menu item
    this.updateActiveMenuItem(this.router.url);
  }

  /**
   * Update active menu item based on current route
   */
  private updateActiveMenuItem(url: string): void {
    this.menuItems.forEach(item => {
      if (item.link) {
        item.isActive = item.link === url || url.startsWith(item.link);
      } else {
        item.isActive = false;
      }
    });
  }

  /**
   * Navigate to menu item
   */
  navigateToItem(item: MenuItem): void {
    if (item.link) {
      this.router.navigate([item.link]);
    }
  }

  /**
   * Toggle submenu (for future use)
   */
  toggleSubmenu(item: MenuItem): void {
    if (item.subItems) {
      item.isCollapsed = !item.isCollapsed;
    }
  }

  /**
   * Navigate to camera
   */
  openCamera(): void {
    this.router.navigate(['/camera']);
    this.hideSidebarOnMobile();
  }

  /**
   * Hide sidebar on mobile after navigation
   */
  hideSidebarOnMobile(): void {
    if (window.innerWidth <= 768) {
      document.body.classList.remove('vertical-sidebar-enable');
      // Also remove hamburger animation
      document.querySelector('.hamburger-icon')?.classList.remove('open');
    }
  }
}
