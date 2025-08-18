import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface CameraConstraints {
  video: {
    facingMode: string;
    width: { ideal: number };
    height: { ideal: number };
  };
}

@Injectable({
  providedIn: 'root'
})
export class CameraService {
  private videoStream: MediaStream | null = null;
  private currentFacingMode = 'user'; // 'user' for front camera, 'environment' for back
  private cameraActiveSubject = new BehaviorSubject<boolean>(false);
  public cameraActive$ = this.cameraActiveSubject.asObservable();

  constructor() { }

  /**
   * Initialize camera with specified constraints
   */
  async initializeCamera(facingMode: string = 'user'): Promise<MediaStream> {
    try {
      // Stop existing stream if any
      if (this.videoStream) {
        this.stopCamera();
      }

      const constraints: CameraConstraints = {
        video: {
          facingMode: facingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      };

      this.videoStream = await navigator.mediaDevices.getUserMedia(constraints);
      this.currentFacingMode = facingMode;
      this.cameraActiveSubject.next(true);
      
      return this.videoStream;
    } catch (error) {
      console.error('Error accessing camera:', error);
      this.cameraActiveSubject.next(false);
      throw new Error('Camera access denied or not available');
    }
  }

  /**
   * Switch between front and back camera
   */
  async switchCamera(): Promise<MediaStream> {
    const newFacingMode = this.currentFacingMode === 'user' ? 'environment' : 'user';
    return await this.initializeCamera(newFacingMode);
  }

  /**
   * Capture image from video stream
   */
  captureImage(videoElement: HTMLVideoElement): string {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (!context) {
      throw new Error('Canvas context not available');
    }

    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    
    // Return base64 encoded image
    return canvas.toDataURL('image/jpeg', 0.8);
  }

  /**
   * Stop camera stream
   */
  stopCamera(): void {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => {
        track.stop();
      });
      this.videoStream = null;
      this.cameraActiveSubject.next(false);
    }
  }

  /**
   * Check if camera is supported
   */
  isCameraSupported(): boolean {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  }

  /**
   * Get current facing mode
   */
  getCurrentFacingMode(): string {
    return this.currentFacingMode;
  }

  /**
   * Check if camera is currently active
   */
  isCameraActive(): boolean {
    return this.cameraActiveSubject.value;
  }
}
