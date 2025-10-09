import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface QuestionRecommendations {
  success: boolean;
  artifact_name: string;
  questions: {
    same_intent_species: string[];
    diff_intent_same_species: string[];
    diff_species_same_intent: string[];
    diff_species_intent: string[];
  };
}

export interface QuestionRecommendationRequest {
  artifact_name: string;
  question?: string;
}

@Injectable({
  providedIn: 'root'
})
export class QuestionRecommenderService {
  private apiUrl = `${environment.apiUrl}/v1/question-recommender`;

  constructor(private http: HttpClient) {}

  /**
   * Get question recommendations for an artifact
   * Note: JWT token is automatically added by JwtInterceptor
   */
  getRecommendations(artifactName: string, question?: string): Observable<QuestionRecommendations> {
    const request: QuestionRecommendationRequest = {
      artifact_name: artifactName
    };
    
    if (question) {
      request.question = question;
    }

    return this.http.post<QuestionRecommendations>(
      `${this.apiUrl}/suggestions`,
      request
    ).pipe(
      catchError(error => {
        console.error('Error fetching question recommendations:', error);
        // Return empty recommendations on error (silent failure)
        return throwError(() => error);
      })
    );
  }

  /**
   * Get the status of the question recommender service
   */
  getStatus(): Observable<any> {
    return this.http.get(`${this.apiUrl}/status`).pipe(
      catchError(error => {
        console.error('Error fetching recommender status:', error);
        return throwError(() => error);
      })
    );
  }
}
