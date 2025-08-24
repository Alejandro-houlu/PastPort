import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { 
  PredictionResponse, 
  CaptureRequest, 
  RecognitionResult 
} from '../Models/mainCam-recognition.models';

@Injectable({
  providedIn: 'root'
})
export class MainCamRecognitionService {
  private readonly baseUrl = `${environment.apiUrl}/v1/mainCam`;

  constructor(private http: HttpClient) {}

  /**
   * Get health status of the recognition service
   */
  getHealth(): Observable<any> {
    return this.http.get(`${this.baseUrl}/health`).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Get supported models
   */
  getSupportedModels(): Observable<any> {
    return this.http.get(`${this.baseUrl}/models`).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Process captured image from camera
   */
  processCapture(request: CaptureRequest): Observable<RecognitionResult> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    return this.http.post<PredictionResponse>(`${this.baseUrl}/capture`, request, { headers }).pipe(
      map(response => {
        if (response.success && response.data) {
          return response.data;
        } else {
          throw new Error(response.error || 'Recognition failed');
        }
      }),
      catchError(this.handleError)
    );
  }

  /**
   * Process image from base64 data
   */
  processBase64Image(request: CaptureRequest): Observable<RecognitionResult> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    return this.http.post<PredictionResponse>(`${this.baseUrl}/predict/base64`, request, { headers }).pipe(
      map(response => {
        if (response.success && response.data) {
          return response.data;
        } else {
          throw new Error(response.error || 'Recognition failed');
        }
      }),
      catchError(this.handleError)
    );
  }

  /**
   * Process uploaded image file
   */
  processUploadedFile(
    file: File, 
    modelName: string = 'yolo11n-seg-custom-v7.pt',
    confidence: number = 0.25,
    iouThreshold: number = 0.45
  ): Observable<RecognitionResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_name', modelName);
    formData.append('confidence', confidence.toString());
    formData.append('iou_threshold', iouThreshold.toString());

    return this.http.post<PredictionResponse>(`${this.baseUrl}/predict/upload`, formData).pipe(
      map(response => {
        if (response.success && response.data) {
          return response.data;
        } else {
          throw new Error(response.error || 'Recognition failed');
        }
      }),
      catchError(this.handleError)
    );
  }

  /**
   * Process image from URL
   */
  processImageUrl(
    imageUrl: string,
    modelName: string = 'yolo11n-seg-custom-v7.pt',
    confidence: number = 0.25,
    iouThreshold: number = 0.45
  ): Observable<RecognitionResult> {
    const params = {
      image_url: imageUrl,
      model_name: modelName,
      confidence: confidence.toString(),
      iou_threshold: iouThreshold.toString()
    };

    return this.http.post<PredictionResponse>(`${this.baseUrl}/predict/url`, null, { params }).pipe(
      map(response => {
        if (response.success && response.data) {
          return response.data;
        } else {
          throw new Error(response.error || 'Recognition failed');
        }
      }),
      catchError(this.handleError)
    );
  }

  /**
   * Convert canvas to base64 image data
   */
  canvasToBase64(canvas: HTMLCanvasElement, quality: number = 0.8): string {
    return canvas.toDataURL('image/jpeg', quality);
  }

  /**
   * Convert video frame to base64 image data
   */
  videoFrameToBase64(video: HTMLVideoElement, quality: number = 0.8): string {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      throw new Error('Could not get canvas context');
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    return canvas.toDataURL('image/jpeg', quality);
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: any): Observable<never> {
    console.error('MainCam Recognition Service Error:', error);
    
    let errorMessage = 'An unknown error occurred';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
      if (error.error && error.error.detail) {
        errorMessage += `\nDetails: ${error.error.detail}`;
      }
    }
    
    return throwError(() => new Error(errorMessage));
  }
}
