import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil } from 'rxjs';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { ArtifactService, Artifact } from '../../Services/artifact.service';

@Component({
  selector: 'app-artifact-display',
  standalone: true,
  imports: [CommonModule, NgbNavModule],
  templateUrl: './artifact-display.component.html',
  styleUrls: ['./artifact-display.component.scss']
})
export class ArtifactDisplayComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Artifact data
  artifactId: string | null = null;
  artifact: Artifact | null = null;
  isLoading = true;
  error: string | null = null;

  // UI state
  selectedImageIndex = 0;
  activeTab = 'description';
  activeNavId = 1;

  // Artifact data with UI enhancements (generated from database data)
  artifactData: any = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private artifactService: ArtifactService
  ) {}

  ngOnInit(): void {
    // Get artifact ID from route parameters
    this.route.paramMap
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        this.artifactId = params.get('id');
        this.loadArtifactData();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load artifact data from backend API
   */
  private loadArtifactData(): void {
    if (!this.artifactId) {
      this.error = 'No artifact ID provided';
      this.isLoading = false;
      return;
    }

    this.isLoading = true;
    this.error = null;

    // Call real API with all images
    this.artifactService.getArtifact(this.artifactId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (artifact) => {
          console.log('Artifact loaded from API:', artifact);
          console.log('Image URLs:', artifact.image_urls);
          console.log('Image Keys:', artifact.image_keys);
          
          this.artifact = artifact;
          
          // Build artifact data with UI-specific information (still hardcoded)
          this.artifactData = this.buildArtifactData(artifact);
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading artifact:', error);
          this.error = error.message || 'Failed to load artifact data';
          this.isLoading = false;
        }
      });
  }

  /**
   * Build artifact data with additional display information
   */
  private buildArtifactData(artifact: Artifact): any {
    const displayName = this.getDisplayName(artifact.artifact_name);
    const category = this.getCategory(artifact.artifact_name);
    
    // Use real images from S3 if available, otherwise use placeholder
    const images = artifact.image_urls && artifact.image_urls.length > 0 
      ? artifact.image_urls 
      : this.getImages(artifact.artifact_name, artifact.image_url);
    
    console.log('Building artifact data with images:', images);
    console.log('Using S3 URLs:', artifact.image_urls && artifact.image_urls.length > 0);
    
    return {
      ...artifact,
      display_name: displayName,
      category: category,
      images: images,
      specifications: this.getSpecifications(artifact.artifact_name),
      historical_context: this.getHistoricalContext(artifact.artifact_name),
      conservation_notes: this.getConservationNotes(artifact.artifact_name),
      related_artifacts: this.getRelatedArtifacts(artifact.artifact_name)
    };
  }

  /**
   * Get display name for artifact
   */
  private getDisplayName(artifactName: string): string {
    const nameMap: { [key: string]: string } = {
      'rafflesia': 'Rafflesia - The Corpse Flower',
      'vase': 'Ancient Ceramic Vase',
      'bowl': 'Traditional Bowl',
      'sculpture': 'Stone Sculpture',
      'painting': 'Traditional Painting'
    };
    
    return nameMap[artifactName.toLowerCase()] || 
           artifactName.charAt(0).toUpperCase() + artifactName.slice(1);
  }

  /**
   * Get category for artifact
   */
  private getCategory(artifactName: string): string {
    const categoryMap: { [key: string]: string } = {
      'rafflesia': 'Botanical Specimens',
      'vase': 'Ceramics & Pottery',
      'bowl': 'Ceramics & Pottery',
      'sculpture': 'Sculptures & Carvings',
      'painting': 'Art & Paintings'
    };
    
    return categoryMap[artifactName.toLowerCase()] || 'General Collection';
  }

  /**
   * Get images for artifact
   */
  private getImages(artifactName: string, imageUrl: string | null): string[] {
    if (imageUrl) {
      return [imageUrl];
    }
    
    // Use actual rafflesia images for rafflesia, placeholder for others
    if (artifactName.toLowerCase() === 'rafflesia') {
      return [
        'assets/images/rafflesia.jpg',
        'assets/images/Rafflesia2.jpg'
      ];
    }
    
    // Fallback to placeholder for other artifacts
    return [
      'assets/images/rafflesia.jpg' // Use rafflesia as default until other images are available
    ];
  }

  /**
   * Get specifications for artifact
   */
  private getSpecifications(artifactName: string): any {
    const specsMap: { [key: string]: any } = {
      'rafflesia': {
        'Scientific Name': 'Rafflesia arnoldii',
        'Family': 'Rafflesiaceae',
        'Size': 'Up to 1 meter across',
        'Weight': 'Up to 11 kg (24 pounds)',
        'Habitat': 'Tropical rainforests of Sumatra and Borneo',
        'Conservation Status': 'Vulnerable'
      }
    };
    
    return specsMap[artifactName.toLowerCase()] || {
      'Type': 'Museum Artifact',
      'Collection': 'General',
      'Status': 'On Display'
    };
  }

  /**
   * Get historical context
   */
  private getHistoricalContext(artifactName: string): string {
    const contextMap: { [key: string]: string } = {
      'rafflesia': 'Named after Sir Stamford Raffles and Dr. Joseph Arnold, Rafflesia represents one of nature\'s most extraordinary adaptations. This parasitic plant has evolved to produce the world\'s largest individual flower, playing a crucial role in Southeast Asian rainforest ecosystems.'
    };
    
    return contextMap[artifactName.toLowerCase()] || 
           'This artifact represents an important piece of cultural and natural heritage, contributing to our understanding of history and biodiversity.';
  }

  /**
   * Get conservation notes
   */
  private getConservationNotes(artifactName: string): string {
    return 'This specimen is carefully preserved using modern conservation techniques to ensure its long-term preservation for future generations.';
  }

  /**
   * Get related artifacts
   */
  private getRelatedArtifacts(artifactName: string): any[] {
    return [
      { id: 'orchid', name: 'Singapore Orchid', image: 'assets/images/rafflesia.jpg' },
      { id: 'pitcher-plant', name: 'Pitcher Plant', image: 'assets/images/Rafflesia2.jpg' },
      { id: 'fern', name: 'Ancient Fern', image: 'assets/images/rafflesia.jpg' }
    ];
  }

  /**
   * Generate random ID
   */
  private generateId(): string {
    return Math.random().toString(36).substr(2, 8);
  }

  /**
   * Handle image selection
   */
  selectImage(index: number): void {
    this.selectedImageIndex = index;
  }

  /**
   * Handle tab selection
   */
  selectTab(tab: string): void {
    this.activeTab = tab;
  }

  /**
   * Navigate back to camera
   */
  goBackToCamera(): void {
    this.router.navigate(['/camera']);
  }

  /**
   * Navigate to related artifact
   */
  viewRelatedArtifact(artifactId: string): void {
    this.router.navigate(['/artifact', artifactId]);
  }

  /**
   * Open chat with current artifact context
   * Note: Click recording is done in main-cam component when user first clicks artifact
   */
  openChat(): void {
    if (this.artifact && this.artifact.id) {
      // Navigate to chat with artifact ID parameter
      this.router.navigate(['/chat', this.artifact.id]);
    } else {
      // Navigate to general chat
      this.router.navigate(['/chat']);
    }
  }

  /**
   * Add to tour (placeholder)
   */
  addToTour(): void {
    console.log('Add to tour functionality - to be implemented');
    // TODO: Implement tour functionality
  }

  /**
   * Share artifact (placeholder)
   */
  shareArtifact(): void {
    console.log('Share artifact functionality - to be implemented');
    // TODO: Implement sharing functionality
  }
}
