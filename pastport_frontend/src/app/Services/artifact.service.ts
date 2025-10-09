import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';

/**
 * Artifact interface matching backend database schema
 */
export interface Artifact {
  id: string;
  artifact_name: string;
  description: string;
  museum_location: string;
  artifact_location: string | null;
  image_url: string | null;
  isDisplay: number | boolean;
  display_startDate: string | null;
  created_at: string;
  updated_at: string;
  // Additional fields from S3
  image_urls?: string[];
  image_keys?: string[];
}

@Injectable({
  providedIn: 'root'
})
export class ArtifactService {
  private readonly API_BASE_URL = `${environment.apiUrl}/v1/artifacts`;

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  /**
   * Get artifact by name with all images (default)
   * 
   * @param artifactName Name of the artifact (e.g., 'rafflesia')
   * @param includeImages Whether to fetch S3 images (default: true)
   * @param allImages Get all images or just first image (default: true for all)
   * @returns Observable of Artifact with image URLs
   */
  getArtifact(
    artifactName: string,
    includeImages: boolean = true,
    allImages: boolean = true
  ): Observable<Artifact> {
    // Build query parameters
    let params = new HttpParams()
      .set('include_images', includeImages.toString())
      .set('all_images', allImages.toString());

    return this.http.get<Artifact>(`${this.API_BASE_URL}/${artifactName}`, {
      headers: this.authService.getAuthHeaders(),
      params: params
    }).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Get artifact with only the first image (for thumbnails)
   * 
   * @param artifactName Name of the artifact
   * @returns Observable of Artifact with first image only
   */
  getArtifactWithFirstImage(artifactName: string): Observable<Artifact> {
    return this.getArtifact(artifactName, true, false);
  }

  /**
   * Get artifact without images
   * 
   * @param artifactName Name of the artifact
   * @returns Observable of Artifact without image URLs
   */
  getArtifactWithoutImages(artifactName: string): Observable<Artifact> {
    return this.getArtifact(artifactName, false, false);
  }

  /**
   * Handle HTTP errors
   * 
   * @param error HTTP error response
   * @returns Observable error
   */
  private handleError(error: any): Observable<never> {
    console.error('Artifact service error:', error);
    
    let errorMessage = 'An error occurred while fetching artifact data';
    
    if (error.status === 404) {
      errorMessage = error.error?.detail || 'Artifact not found';
    } else if (error.status === 401) {
      errorMessage = 'Authentication required. Please log in again.';
    } else if (error.status === 500) {
      errorMessage = 'Server error. Please try again later.';
    } else if (error.error?.detail) {
      errorMessage = error.error.detail;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    return throwError(() => new Error(errorMessage));
  }
}
