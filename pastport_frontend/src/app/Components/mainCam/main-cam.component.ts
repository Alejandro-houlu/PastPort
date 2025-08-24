import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { CameraService } from '../../Services/camera.service';
import { MainCamRecognitionService } from '../../Services/mainCam-recognition.service';
import { MainCamWebSocketService } from '../../Services/mainCam-websocket.service';
import { MainCamVisualizationService } from '../../Services/mainCam-visualization.service';
import { RecognitionResult } from '../../Models/mainCam-recognition.models';

@Component({
  selector: 'app-main-cam',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './main-cam.component.html',
  styleUrls: ['./main-cam.component.scss']
})
export class MainCamComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('overlayCanvas', { static: false }) overlayCanvas!: ElementRef<HTMLCanvasElement>;

  // UI State
  isLoading = false;
  currentFacingMode = 'environment'; // Default to rear camera for mobile
  lastCapturedImage: string | null = null;
  showSidebar = false;
  cameraActive = false;

  // Recognition State
  recognitionActive = false;
  isConnected = false;
  lastRecognitionResult: RecognitionResult | null = null;
  detectionCount = 0;

  constructor(
    private router: Router,
    private cameraService: CameraService,
    private recognitionService: MainCamRecognitionService,
    private websocketService: MainCamWebSocketService,
    private visualizationService: MainCamVisualizationService
  ) {}

  ngOnInit(): void {
    // Initialize WebSocket connection first
    this.initializeRecognition();
  }

  ngAfterViewInit(): void {
    // Initialize camera after view is ready
    this.initializeCamera();
  }

  ngOnDestroy(): void {
    // Cleanup camera resources
    this.cleanup();
  }

  /**
   * Initialize camera
   */
  private async initializeCamera(): Promise<void> {
    try {
      this.isLoading = true;
      console.log('📹 Starting camera initialization...');
      
      // Check if camera is supported
      if (!this.cameraService.isCameraSupported()) {
        console.error('Camera not supported');
        return;
      }

      // Initialize camera with rear camera (environment) by default
      const stream = await this.cameraService.initializeCamera(this.currentFacingMode);
      
      // Set up video element and wait for it to be ready
      await this.setupVideoElement(stream);
      
      console.log('✅ Camera initialized successfully');

    } catch (error) {
      console.error('Error initializing camera:', error);
      // Fallback to front camera if rear camera fails
      if (this.currentFacingMode === 'environment') {
        console.log('Rear camera failed, trying front camera...');
        this.currentFacingMode = 'user';
        try {
          const stream = await this.cameraService.initializeCamera(this.currentFacingMode);
          await this.setupVideoElement(stream);
          console.log('✅ Front camera initialized successfully');
        } catch (fallbackError) {
          console.error('Both cameras failed:', fallbackError);
        }
      }
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Set up video element with stream and wait for it to be ready
   */
  private setupVideoElement(stream: MediaStream): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.videoElement?.nativeElement) {
        reject(new Error('Video element not available'));
        return;
      }

      const video = this.videoElement.nativeElement;
      
      // Set up event listeners
      const onLoadedMetadata = () => {
        console.log('📹 Video metadata loaded, camera is ready');
        this.cameraActive = true;
        this.checkAndStartRecognition();
        video.removeEventListener('loadedmetadata', onLoadedMetadata);
        video.removeEventListener('error', onError);
        resolve();
      };

      const onError = (error: Event) => {
        console.error('Video element error:', error);
        video.removeEventListener('loadedmetadata', onLoadedMetadata);
        video.removeEventListener('error', onError);
        reject(new Error('Video element failed to load'));
      };

      video.addEventListener('loadedmetadata', onLoadedMetadata);
      video.addEventListener('error', onError);

      // Set stream and play
      video.srcObject = stream;
      video.play().catch(playError => {
        console.error('Error playing video:', playError);
        reject(playError);
      });
    });
  }

  /**
   * Check if both camera and WebSocket are ready, then start recognition
   */
  private checkAndStartRecognition(): void {
    console.log('🔍 Checking readiness - Camera:', this.cameraActive, 'WebSocket:', this.isConnected);
    
    if (this.cameraActive && this.isConnected && !this.recognitionActive) {
      console.log('🎬 Both systems ready - starting recognition');
      this.startRecognition();
    }
  }

  /**
   * Handle capture button click - placeholder
   */
  onCapturePhoto(): void {
    console.log('Capture photo clicked - placeholder for WebSocket implementation');
    // Future: WebSocket communication for photo capture
  }

  /**
   * Handle camera flip button click
   */
  async onFlipCamera(): Promise<void> {
    try {
      this.isLoading = true;
      console.log('Flipping camera...');
      
      // Switch camera using the camera service
      const stream = await this.cameraService.switchCamera();
      this.currentFacingMode = this.cameraService.getCurrentFacingMode();
      
      // Update video element with new stream
      if (this.videoElement?.nativeElement) {
        this.videoElement.nativeElement.srcObject = stream;
        this.videoElement.nativeElement.play();
        console.log(`Camera switched to: ${this.currentFacingMode}`);
      }
    } catch (error) {
      console.error('Error switching camera:', error);
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Handle last image click - navigate to photo album
   */
  onLastImageClick(): void {
    console.log('Last image clicked - placeholder for photo album navigation');
    // Future: Navigate to photo album component
  }

  /**
   * Toggle sidebar visibility
   */
  toggleSidebar(): void {
    this.showSidebar = !this.showSidebar;
  }

  /**
   * Close sidebar
   */
  closeSidebar(): void {
    this.showSidebar = false;
  }

  /**
   * Navigate back to dashboard
   */
  goBack(): void {
    this.router.navigate(['/dashboard']);
  }

  /**
   * Initialize recognition system
   */
  private async initializeRecognition(): Promise<void> {
    console.log('🚀 Initializing MainCam recognition system...');
    try {
      // Connect to WebSocket for real-time recognition
      console.log('🔗 Connecting to WebSocket for real-time recognition...');
      await this.websocketService.connect();
      this.isConnected = true;
      console.log('✅ WebSocket connection established');
      
      // Subscribe to recognition results
      this.websocketService.getRecognitionResults().subscribe({
        next: (result) => {
          console.log('🎯 Received recognition result:', {
            detections: result.metadata.num_detections,
            processing_time: result.metadata.processing_time + 'ms',
            artifacts: result.detections.map(d => `${d.class_name} (${(d.confidence * 100).toFixed(1)}%)`)
          });
          this.lastRecognitionResult = result;
          this.detectionCount = result.metadata.num_detections;
          this.drawRecognitionOverlay(result);
        },
        error: (error) => {
          console.error('❌ Error in recognition results stream:', error);
        }
      });

      // Subscribe to connection status
      this.websocketService.getConnectionStatus().subscribe({
        next: (connected) => {
          console.log('📡 WebSocket connection status changed:', connected);
          this.isConnected = connected;
          
          if (!connected && this.recognitionActive) {
            console.log('⚠️ WebSocket disconnected, stopping recognition');
            this.stopRecognition();
          }
          
          this.checkAndStartRecognition();
        },
        error: (error) => {
          console.error('❌ Error in connection status stream:', error);
        }
      });

      // Subscribe to errors
      this.websocketService.getErrors().subscribe({
        next: (error) => {
          console.error('❌ WebSocket error received:', error);
          // Could add user notification here
        },
        error: (streamError) => {
          console.error('❌ Error in error stream:', streamError);
        }
      });

      // Initial ready state check
      this.checkAndStartRecognition();

    } catch (error) {
      console.error('💥 Failed to initialize recognition:', error);
      this.isConnected = false;
      // Could add user notification here
    }
  }

  /**
   * Start real-time recognition
   */
  private startRecognition(): void {
    console.log('🎬 Starting recognition...');
    
    if (!this.isConnected) {
      console.warn('⚠️ Cannot start recognition - WebSocket not connected');
      return;
    }

    if (!this.videoElement?.nativeElement) {
      console.warn('⚠️ Cannot start recognition - Video element not available');
      return;
    }

    if (this.recognitionActive) {
      console.log('ℹ️ Recognition already active, skipping start');
      return;
    }

    const video = this.videoElement.nativeElement;
    console.log('📹 Video ready state:', video.readyState, 'Video dimensions:', video.videoWidth, 'x', video.videoHeight);

    this.recognitionActive = true;
    
    // Wait for video to be ready
    if (video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0) {
      console.log('✅ Video ready, starting frame streaming at 5 FPS');
      this.websocketService.startFrameStreaming(video, 5); // 5 FPS
    } else {
      console.log('⏳ Video not ready, waiting for loadedmetadata event');
      const onMetadataLoaded = () => {
        console.log('📹 Video metadata loaded, starting frame streaming');
        this.websocketService.startFrameStreaming(video, 5);
        video.removeEventListener('loadedmetadata', onMetadataLoaded);
      };
      video.addEventListener('loadedmetadata', onMetadataLoaded);
    }
  }

  /**
   * Stop real-time recognition
   */
  private stopRecognition(): void {
    this.recognitionActive = false;
    this.websocketService.stopFrameStreaming();
    this.clearOverlay();
  }

  /**
   * Draw recognition overlay on canvas
   */
  private drawRecognitionOverlay(result: RecognitionResult): void {
    if (!this.overlayCanvas?.nativeElement || !this.videoElement?.nativeElement) {
      console.warn('⚠️ Canvas or video element not available for overlay');
      return;
    }

    const canvas = this.overlayCanvas.nativeElement;
    const video = this.videoElement.nativeElement;

    console.log(`🎬 Drawing overlay - Video ready state: ${video.readyState}`);
    console.log(`📺 Video dimensions: ${video.videoWidth}x${video.videoHeight} (display: ${video.clientWidth}x${video.clientHeight})`);

    // Update canvas size to match video
    this.visualizationService.updateCanvasSize(canvas, video);

    // Draw recognition results
    this.visualizationService.drawRecognitionResults(canvas, result, {
      showBoxes: false, // Remove bounding boxes - only show masks and labels
      showLabels: true,
      showConfidence: true,
      showMasks: true,
      boxColor: '#ad64f1',
      labelBackgroundColor: '#ad64f1',
      minConfidence: 0.3
    });
  }

  /**
   * Clear overlay canvas
   */
  private clearOverlay(): void {
    if (this.overlayCanvas?.nativeElement) {
      this.visualizationService.clearOverlay(this.overlayCanvas.nativeElement);
    }
  }

  /**
   * Capture single image for analysis
   */
  async captureAndAnalyze(): Promise<void> {
    if (!this.videoElement?.nativeElement) {
      return;
    }

    try {
      this.isLoading = true;
      
      // Convert video frame to base64
      const frameData = this.recognitionService.videoFrameToBase64(
        this.videoElement.nativeElement, 
        0.9 // High quality for single image
      );

      // Process with recognition service
      this.recognitionService.processCapture({
        image_data: frameData,
        model_name: 'yolo11n-seg-custom-v7.pt',
        confidence: 0.25,
        iou_threshold: 0.45
      }).subscribe({
        next: (result) => {
          // Update UI with results
          this.lastRecognitionResult = result;
          this.detectionCount = result.metadata.num_detections;
          this.drawRecognitionOverlay(result);
          console.log('Capture analysis complete:', result);
        },
        error: (error) => {
          console.error('Error analyzing captured image:', error);
        },
        complete: () => {
          this.isLoading = false;
        }
      });

    } catch (error) {
      console.error('Error analyzing captured image:', error);
      this.isLoading = false;
    }
  }

  /**
   * Toggle recognition on/off
   */
  toggleRecognition(): void {
    if (this.recognitionActive) {
      this.stopRecognition();
    } else {
      this.startRecognition();
    }
  }

  /**
   * Cleanup resources
   */
  private cleanup(): void {
    console.log('Cleaning up camera and recognition resources...');
    this.stopRecognition();
    this.websocketService.cleanup();
    this.cameraService.stopCamera();
    this.cameraActive = false;
    this.isConnected = false;
  }
}
