import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from './navbar/navbar.component';
import { SidebarComponent } from './sidebar/sidebar.component';
import { FooterComponent } from './footer/footer.component';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent, SidebarComponent, FooterComponent],
  templateUrl: './layout.component.html',
  styleUrls: ['./layout.component.scss']
})
export class LayoutComponent implements OnInit {
  
  isCondensed = false;
  isMobileMenuOpen = false;

  constructor() {}

  ngOnInit(): void {
    // Initialize layout
    this.initializeLayout();
  }

  /**
   * Initialize layout settings
   */
  private initializeLayout(): void {
    // Set default layout attributes for PastPort
    document.documentElement.setAttribute('data-layout', 'vertical');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
    document.documentElement.setAttribute('data-sidebar-size', 'lg');
    document.documentElement.setAttribute('data-layout-width', 'fluid');
    document.documentElement.setAttribute('data-layout-position', 'fixed');
    document.documentElement.setAttribute('data-topbar', 'dark');
    document.documentElement.setAttribute('data-sidebar', 'dark');
  }

  /**
   * Toggle mobile menu
   */
  onToggleMobileMenu(): void {
    const currentSidebarSize = document.documentElement.getAttribute("data-sidebar-size");
    
    if (document.documentElement.clientWidth >= 768) {
      // Desktop: Toggle sidebar size
      if (currentSidebarSize === "lg") {
        document.documentElement.setAttribute('data-sidebar-size', 'sm');
      } else {
        document.documentElement.setAttribute('data-sidebar-size', 'lg');
      }
    } else {
      // Mobile: Toggle sidebar visibility
      document.body.classList.toggle('vertical-sidebar-enable');
      this.isMobileMenuOpen = !this.isMobileMenuOpen;
    }
    
    this.isCondensed = !this.isCondensed;
  }

  /**
   * Close mobile sidebar (following TravelDx pattern)
   */
  closeMobileSidebar(): void {
    document.body.classList.remove('vertical-sidebar-enable');
    document.querySelector('.hamburger-icon')?.classList.remove('open');
    this.isMobileMenuOpen = false;
  }

  /**
   * Handle window resize
   */
  onResize(event: any): void {
    if (event.target.innerWidth <= 768) {
      document.documentElement.setAttribute('data-sidebar-size', 'lg');
      document.body.classList.remove('vertical-sidebar-enable');
      this.isMobileMenuOpen = false;
    }
  }
}
