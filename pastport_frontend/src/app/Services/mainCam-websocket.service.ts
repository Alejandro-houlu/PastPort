import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';
import { 
  WebSocketMessage, 
  WebSocketResponse, 
  RecognitionConfig, 
  RecognitionResult 
} from '../Models/mainCam-recognition.models';

@Injectable({
  providedIn: 'root'
})
export class MainCamWebSocketService {
  private socket: WebSocket | null = null;
  private readonly wsUrl = `${environment.wsUrl}/ws/mainCam`;
  
  // Subjects for different message types
  private connectionStatus$ = new BehaviorSubject<boolean>(false);
  private recognitionResults$ = new Subject<RecognitionResult>();
  private errors$ = new Subject<string>();
  private configUpdates$ = new Subject<RecognitionConfig>();
  
  // Frame tracking
  private frameId = 0;
  private isProcessing = false;
  private streamingIntervalId: any = null;
  
  // Default configuration
  private currentConfig: RecognitionConfig = {
    model_name: 'yolo11n-seg-custom-v7.pt',
    confidence: 0.25,
    iou_threshold: 0.45
  };

  constructor() {}

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    console.log('🔌 Attempting to connect to WebSocket:', this.wsUrl);
    
    // Disconnect existing connection if any
    if (this.socket) {
      console.log('🔄 Closing existing WebSocket connection before creating new one');
      this.disconnect();
    }
    
    // Reset state before connecting
    this.isProcessing = false;
    this.frameId = 0;
    
    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(this.wsUrl);
        
        this.socket.onopen = () => {
          console.log('✅ MainCam WebSocket connected successfully');
          console.log('📡 Sending initial config:', this.currentConfig);
          this.connectionStatus$.next(true);
          this.sendConfig(this.currentConfig);
          resolve();
        };
        
        this.socket.onmessage = (event) => {
          this.handleMessage(event.data);
        };
        
        this.socket.onclose = (event) => {
          console.log('🔌 MainCam WebSocket disconnected:', event.code, event.reason);
          this.connectionStatus$.next(false);
          this.socket = null;
          // Reset processing state on close
          this.isProcessing = false;
        };
        
        this.socket.onerror = (error) => {
          console.error('💥 MainCam WebSocket error:', error);
          this.errors$.next('WebSocket connection error');
          // Reset processing state on error
          this.isProcessing = false;
          reject(error);
        };
        
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      console.log('🔌 Disconnecting WebSocket...');
      this.socket.close();
      this.socket = null;
      this.connectionStatus$.next(false);
      // Reset processing state on disconnect
      this.isProcessing = false;
      this.frameId = 0;
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection status observable
   */
  getConnectionStatus(): Observable<boolean> {
    return this.connectionStatus$.asObservable();
  }

  /**
   * Get recognition results observable
   */
  getRecognitionResults(): Observable<RecognitionResult> {
    return this.recognitionResults$.asObservable();
  }

  /**
   * Get errors observable
   */
  getErrors(): Observable<string> {
    return this.errors$.asObservable();
  }

  /**
   * Get config updates observable
   */
  getConfigUpdates(): Observable<RecognitionConfig> {
    return this.configUpdates$.asObservable();
  }

  /**
   * Send configuration to server
   */
  sendConfig(config: RecognitionConfig): void {
    if (!this.isConnected()) {
      console.warn('WebSocket not connected, cannot send config');
      return;
    }

    this.currentConfig = { ...config };
    
    const message: WebSocketMessage = {
      type: 'config',
      config: config
    };

    this.sendMessage(message);
  }

  /**
   * Send video frame for recognition
   */
  sendFrame(frameData: string): void {
    if (!this.isConnected()) {
      console.warn('⚠️ WebSocket not connected, cannot send frame');
      // Reset processing state if connection is lost
      this.isProcessing = false;
      return;
    }

    if (this.isProcessing) {
      // Skip frame if still processing previous one
      console.log('⏭️ Skipping frame - still processing previous frame');
      return;
    }

    this.isProcessing = true;
    this.frameId++;

    const message: WebSocketMessage = {
      type: 'frame',
      frame_data: frameData,
      frame_id: this.frameId,
      timestamp: Date.now()
    };

    console.log(`📸 Sending frame ${this.frameId} for recognition`);
    this.sendMessage(message);
  }

  /**
   * Send ping to server
   */
  sendPing(): void {
    if (!this.isConnected()) {
      return;
    }

    const message: WebSocketMessage = {
      type: 'ping',
      timestamp: Date.now()
    };

    this.sendMessage(message);
  }

  /**
   * Update recognition configuration
   */
  updateConfig(config: Partial<RecognitionConfig>): void {
    const newConfig = { ...this.currentConfig, ...config };
    this.sendConfig(newConfig);
  }

  /**
   * Get current configuration
   */
  getCurrentConfig(): RecognitionConfig {
    return { ...this.currentConfig };
  }

  /**
   * Send message to WebSocket server
   */
  private sendMessage(message: WebSocketMessage): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      try {
        this.socket.send(JSON.stringify(message));
      } catch (error) {
        console.error('💥 Error sending WebSocket message:', error);
        // Reset processing state if sending fails
        if (message.type === 'frame') {
          this.isProcessing = false;
        }
        this.errors$.next('Failed to send message to server');
      }
    } else {
      console.warn('⚠️ Cannot send message - WebSocket not connected');
      // Reset processing state if connection is lost
      if (message.type === 'frame') {
        this.isProcessing = false;
      }
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: string): void {
    try {
      const message: WebSocketResponse = JSON.parse(data);
      console.log('📨 Received WebSocket message:', message.type);
      
      switch (message.type) {
        case 'config_updated':
          console.log('⚙️ Config updated:', message.config);
          if (message.config) {
            this.currentConfig = message.config;
            this.configUpdates$.next(message.config);
          }
          break;
          
        case 'recognition_result':
          this.isProcessing = false;
          if (message.result) {
            console.log(`🎯 Recognition result for frame ${message.frame_id}:`, {
              detections: message.result.metadata.num_detections,
              processing_time: message.result.metadata.processing_time,
              classes: message.result.detections.map(d => d.class_name)
            });
            this.recognitionResults$.next(message.result);
          }
          break;
          
        case 'pong':
          console.log('🏓 Received pong from server');
          break;
          
        case 'error':
          this.isProcessing = false;
          const errorMsg = message.message || 'Unknown WebSocket error';
          console.error('❌ WebSocket error:', errorMsg);
          this.errors$.next(errorMsg);
          // If error is related to frame processing, ensure we can continue
          if (errorMsg.includes('Frame processing error')) {
            console.log('🔄 Frame processing error detected, resetting processing state');
          }
          break;
          
        default:
          console.warn('❓ Unknown message type:', message.type);
      }
      
    } catch (error) {
      console.error('💥 Failed to parse WebSocket message:', error);
      this.errors$.next('Failed to parse server message');
      // Reset processing state on parse error to prevent getting stuck
      this.isProcessing = false;
    }
  }

  /**
   * Convert video element to base64 frame data
   */
  videoToFrameData(video: HTMLVideoElement, quality: number = 0.8): string {
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
   * Start automatic frame sending from video element
   */
  startFrameStreaming(video: HTMLVideoElement, fps: number = 5): void {
    if (!this.isConnected()) {
      console.warn('WebSocket not connected, cannot start streaming');
      return;
    }

    const interval = 1000 / fps; // Convert FPS to milliseconds
    
    const sendFrame = () => {
      if (this.isConnected() && video.readyState >= 2) {
        try {
          const frameData = this.videoToFrameData(video);
          this.sendFrame(frameData);
        } catch (error) {
          console.error('Error capturing video frame:', error);
        }
      }
    };

    // Start sending frames at specified FPS
    const intervalId = setInterval(sendFrame, interval);
    
    // Store interval ID for cleanup
    this.streamingIntervalId = intervalId;
  }

  /**
   * Stop automatic frame sending
   */
  stopFrameStreaming(): void {
    if (this.streamingIntervalId) {
      clearInterval(this.streamingIntervalId);
      this.streamingIntervalId = null;
    }
  }

  /**
   * Force reset processing state - useful for recovery
   */
  forceResetProcessingState(): void {
    console.log('🔄 Force resetting processing state');
    this.isProcessing = false;
  }

  /**
   * Get current processing state
   */
  getProcessingState(): boolean {
    return this.isProcessing;
  }

  /**
   * Reset connection state completely
   */
  resetConnectionState(): void {
    console.log('🔄 Resetting all connection state');
    this.isProcessing = false;
    this.frameId = 0;
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    console.log('🧹 Cleaning up WebSocket service');
    this.stopFrameStreaming();
    this.disconnect();
    this.resetConnectionState();
  }
}
