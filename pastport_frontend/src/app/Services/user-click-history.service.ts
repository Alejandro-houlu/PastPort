import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface ClickRecordRequest {
  artifact_name: string;
  source?: string;
}

export interface ClickRecordResponse {
  success: boolean;
  message: string;
  click_id: string;
}

export interface ArtifactClick {
  id: string;
  artifact_name: string;
  description: string | null;
  museum_location: string | null;
  artifact_location: string | null;
  image_url: string | null;
  isDisplay: boolean;
  clicked_at: string;
}

export interface ChatHistoryItem {
  session_id: string;
  artifact_id: string | null;
  artifact_name: string | null;
  last_message: string;
  timestamp: string;
  message_count: number;
}

@Injectable({
  providedIn: 'root'
})
export class UserClickHistoryService {
  private apiUrl = `${environment.apiUrl}/user-clicks`;
  private chatHistoryUrl = `${environment.apiUrl}/chat-history`;

  constructor(private http: HttpClient) {}

  /**
   * Record a user's click on an artifact
   * User is automatically determined from JWT token by backend
   * Note: JWT token is automatically added by JwtInterceptor
   */
  recordClick(artifactName: string, source: string = 'camera'): Observable<ClickRecordResponse> {
    const request: ClickRecordRequest = {
      artifact_name: artifactName,
      source: source
    };

    return this.http.post<ClickRecordResponse>(
      `${this.apiUrl}/record`, // Add trailing slash only for POST to match FastAPI route
      request
    ).pipe(
      catchError(error => {
        console.error('Error recording click:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Get recent artifact clicks for a user
   */
  getRecentClicks(userId: string, limit: number = 5): Observable<ArtifactClick[]> {
    return this.http.get<ArtifactClick[]>(
      `${this.apiUrl}/${userId}/recent?limit=${limit}`
    ).pipe(
      catchError(error => {
        console.error('Error fetching recent clicks:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Get user's chat history
   * Note: JWT token is automatically added by JwtInterceptor
   */
  getChatHistory(userId: string, limit: number = 10): Observable<ChatHistoryItem[]> {
    return this.http.get<ChatHistoryItem[]>(
      `${this.chatHistoryUrl}/${userId}?limit=${limit}`
    ).pipe(
      catchError(error => {
        console.error('Error fetching chat history:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Get messages for a specific chat session
   * Note: JWT token is automatically added by JwtInterceptor
   */
  getSessionMessages(sessionId: string): Observable<any> {
    return this.http.get(
      `${this.chatHistoryUrl}/session/${sessionId}`
    ).pipe(
      catchError(error => {
        console.error('Error fetching session messages:', error);
        return throwError(() => error);
      })
    );
  }
}
