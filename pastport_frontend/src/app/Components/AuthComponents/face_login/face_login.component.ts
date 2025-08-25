import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription, firstValueFrom } from 'rxjs';

import { CameraService } from '../../../Services/camera.service';
import { FaceLoginService } from '../../../Services/face-login.service';
import { BiometricConsentService } from '../../../Services/biometric-consent.service';
import { AuthService } from '../../../Services/auth.service';

import { 
  FaceDetectionResult, 
  LivenessResult, 
  FaceRecognitionResult,
  BiometricConsentModal 
} from '../../../Models/face-recognition.models';

export interface FaceLoginState {
  step: 'consent' | 'camera' | 'processing' | 'registration' | 'success' | 'error';
  message: string;
  isLoading: boolean;
  showRetry: boolean;
}

@Component({
  selector: 'app-face-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './face_login.component.html',
  styleUrls: ['./face_login.component.scss']
})
export class FaceLoginComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement', { static: false }) canvasElement!: ElementRef<HTMLCanvasElement>;

  // Component state
  state: FaceLoginState = {
    step: 'consent',
    message: 'Welcome to PastPort Face Recognition',
    isLoading: false,
    showRetry: false
  };

  // Face detection state
  faceDetected = false;
  livenessDetected = false;
  faceQuality = 0;
  
  // Registration state
  tempFaceId = '';
  username = '';
  
  // UI state
  showConsentModal = false;
  consentModalContent: BiometricConsentModal | null = null;
  cameraActive = false;
  facingMode = 'user'; // 'user' for front camera
  
  // Subscriptions
  private subscriptions: Subscription[] = [];
  private detectionInterval: any;
  private livenessCheckInterval: any;

  constructor(
    private router: Router,
    private cameraService: CameraService,
    private faceLoginService: FaceLoginService,
    private biometricConsentService: BiometricConsentService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.initializeComponent();
  }

  ngOnDestroy(): void {
    this.cleanup();
  }

  /**
   * Initialize component and check consent
   */
  private initializeComponent(): void {
    // Check if user has already given consent
    if (this.biometricConsentService.hasValidConsent()) {
      this.proceedToCamera();
    } else {
      this.showConsentModal = true;
      this.consentModalContent = this.biometricConsentService.getConsentModalContent();
    }

    // Load face recognition models
    this.loadFaceModels();
  }

  /**
   * Load face-api.js models
   */
  private async loadFaceModels(): Promise<void> {
    try {
      this.state.isLoading = true;
      this.state.message = 'Loading face recognition models...';
      
      await this.faceLoginService.loadModels();
      
      console.log('Face recognition models loaded successfully');
    } catch (error) {
      console.error('Error loading face models:', error);
      this.handleError('Failed to load face recognition models');
    } finally {
      this.state.isLoading = false;
    }
  }

  /**
   * Handle consent acceptance
   */
  onConsentAccepted(): void {
    this.biometricConsentService.grantConsent();
    this.showConsentModal = false;
    this.proceedToCamera();
  }

  /**
   * Handle consent rejection
   */
  onConsentRejected(): void {
    this.biometricConsentService.revokeConsent();
    this.router.navigate(['/auth/login']); // Redirect to regular login
  }

  /**
   * Proceed to camera interface
   */
  private async proceedToCamera(): Promise<void> {
    this.state.step = 'camera';
    this.state.message = 'Position your face in the circle';
    
    try {
      await this.initializeCamera();
      this.startFaceDetection();
    } catch (error) {
      this.handleError('Camera access denied or not available');
    }
  }

  /**
   * Initialize camera
   */
  private async initializeCamera(): Promise<void> {
    try {
      const stream = await this.cameraService.initializeCamera(this.facingMode);
      
      if (this.videoElement?.nativeElement) {
        this.videoElement.nativeElement.srcObject = stream;
        this.videoElement.nativeElement.play();
        this.cameraActive = true;
      }
    } catch (error) {
      console.error('Error initializing camera:', error);
      throw error;
    }
  }

  /**
   * Start face detection loop
   */
  private startFaceDetection(): void {
    this.detectionInterval = setInterval(async () => {
      if (this.videoElement?.nativeElement && this.cameraActive) {
        await this.detectFace();
      }
    }, 100); // Check every 100ms for smooth detection

    // Start liveness detection (less frequent)
    this.livenessCheckInterval = setInterval(async () => {
      if (this.videoElement?.nativeElement && this.cameraActive && this.faceDetected) {
        await this.checkLiveness();
      }
    }, 500); // Check every 500ms
  }

  /**
   * Detect face in video stream
   */
  private async detectFace(): Promise<void> {
    try {
      if (!this.videoElement?.nativeElement) {
        return;
      }

      const result: FaceDetectionResult = await this.faceLoginService.detectFace(
        this.videoElement.nativeElement
      );

      this.faceDetected = result.isDetected;
      this.faceQuality = result.confidence;

      if (result.isDetected) {
        this.state.message = 'Face detected! Please look directly at the camera';
      } else {
        this.state.message = 'Position your face in the circle';
        this.livenessDetected = false;
      }
    } catch (error) {
      console.error('Error detecting face:', error);
    }
  }

  /**
   * Check liveness
   */
  private async checkLiveness(): Promise<void> {
    try {
      if (!this.videoElement?.nativeElement) {
        return;
      }

      const result: LivenessResult = await this.faceLoginService.performLivenessDetection(
        this.videoElement.nativeElement
      );

      this.livenessDetected = result.isLive;

      if (result.isLive) {
        this.state.message = 'Great! Please hold still...';
        // Auto-capture after successful liveness detection
        setTimeout(() => this.captureAndProcess(), 1000);
      } else {
        if (!result.eyeBlinkDetected) {
          this.state.message = 'Please blink your eyes';
        } else if (!result.headMovementDetected) {
          this.state.message = 'Please move your head slightly';
        } else {
          this.state.message = 'Please look directly at the camera';
        }
      }
    } catch (error) {
      console.error('Error checking liveness:', error);
    }
  }

  /**
   * Capture and process using streamlined authentication flow
   */
  async captureAndProcess(): Promise<void> {
    if(this.state.step === 'processing')return;

    const videoEl = this.videoElement?.nativeElement;

    if (!this.videoElement?.nativeElement) {
      throw new Error('Video element not available');return;
    }

    this.stopDetection();
    this.state.step = 'processing';
    this.state.isLoading = true;
    this.state.message = 'Capturing and analyzing your face...';
    

    try {
      // Check if video element is available

      console.log('🎯 Starting streamlined authentication flow...');
      
      // Use the new streamlined authentication method
      const authResult = await this.faceLoginService.authenticateUser(videoEl);

      console.log('🔍 AUTHENTICATION RESULT - COMPLETE DATA:', {
        isRecognized: authResult.isRecognized,
        isNewUser: authResult.isNewUser,
        requiresUsername: authResult.requiresUsername,
        userId: authResult.userId,
        username: authResult.username,
        confidence: authResult.confidence,
        ageGroup: authResult.ageGroup,
        accessToken: authResult.accessToken ? 'Present (' + authResult.accessToken.substring(0, 20) + '...)' : 'Missing',
        refreshToken: authResult.refreshToken ? 'Present (' + authResult.refreshToken.substring(0, 20) + '...)' : 'Missing',
        userData: authResult.userData
      });

      // Verify tokens are stored properly
      const storedToken = localStorage.getItem('pastport_jwt_token');
      const storedRefreshToken = localStorage.getItem('pastport_refresh_token');

      if (authResult.isRecognized && authResult.username) {
        // User recognized - proceed with login
          console.log('🔐 TOKEN STORAGE VERIFICATION:', {
          accessTokenStored: storedToken ? 'Yes (' + storedToken.substring(0, 20) + '...)' : 'No',
          refreshTokenStored: storedRefreshToken ? 'Yes (' + storedRefreshToken.substring(0, 20) + '...)' : 'No'
        });

        await this.handleRecognizedUser(authResult);
      } else if (authResult.isNewUser && authResult.requiresUsername) {
        // New user detected - ask for username
        await this.handleNewUser(authResult);
      } else {
        // No face detected or other error
        this.handleError('Could not detect face properly. Please try again.');
      }
    } catch (error) {
      console.error('Error in authentication flow:', error);
      this.handleError('Error processing your face. Please try again.');
    }
  }

  /**
   * Handle recognized user login
   */
  private async handleRecognizedUser(authResult: any): Promise<void> {
    try {
      console.log('✅ USER RECOGNIZED:', {
        username: authResult.username,
        confidence: authResult.confidence,
        ageGroup: authResult.ageGroup,
        userId: authResult.userId
      });
      this.state.isLoading = false
      this.state.step = 'success';
      this.state.message = `Welcome back, ${authResult.username}! (Confidence: ${Math.round(authResult.confidence * 100)}%)`;
      
      // Navigate to main app after short delay
      setTimeout(() => {
        console.log('🔄 Redirecting to dashboard');
        this.router.navigate(['/dashboard']);
      }, 800);
    } catch (error) {
      console.error('Error during login:', error);
      this.handleError('Login failed. Please try again.');
    }
  }

  /**
   * Handle new user registration flow
   */
  private async handleNewUser(authResult: any): Promise<void> {
    try {
      console.log('🆕 NEW USER DETECTED:', {
        userId: authResult.userId,
        ageGroup: authResult.ageGroup,
        requiresUsername: authResult.requiresUsername
      });

      this.tempFaceId = authResult.userId || 'temp_' + Date.now();
      this.state.step = 'registration';
      this.state.message = 'New face detected! Please enter your name to create an account.';
      this.state.isLoading = false;
    } catch (error) {
      console.error('Error during new user handling:', error);
      this.handleError('Registration setup failed. Please try again.');
    }
  }

  /**
   * Complete user registration using the new streamlined flow
   */
  async completeRegistration(): Promise<void> {
    if (!this.username.trim()) {
      this.state.message = 'Please enter your name';
      return;
    }

    this.state.isLoading = true;
    this.state.message = 'Creating your account...';

    try {
      console.log('📝 COMPLETING REGISTRATION:', {
        username: this.username.trim(),
        tempFaceId: this.tempFaceId
      });
      
      // Use the backend registration method (pass null since camera is stopped)
      const registrationResult = await this.faceLoginService.registerNewUser(
        null,
        this.username.trim()
      );
      
      if (registrationResult.success) {
        console.log('🎉 REGISTRATION SUCCESS:', registrationResult);
        
        if (registrationResult.authResult) {
          // Registration included authentication - handle as successful login
          console.log('✅ Registration completed with authentication:', {
            username: registrationResult.authResult.username,
            userId: registrationResult.authResult.userId,
            confidence: registrationResult.authResult.confidence,
            accessToken: registrationResult.authResult.accessToken ? 'Present' : 'Missing',
            refreshToken: registrationResult.authResult.refreshToken ? 'Present' : 'Missing'
          });
          
          // Verify tokens are stored properly
          const storedToken = localStorage.getItem('pastport_jwt_token');
          const storedRefreshToken = localStorage.getItem('pastport_refresh_token');
          console.log('🔐 POST-REGISTRATION TOKEN STORAGE:', {
            accessTokenStored: storedToken ? 'Yes (' + storedToken.substring(0, 20) + '...)' : 'No',
            refreshTokenStored: storedRefreshToken ? 'Yes (' + storedRefreshToken.substring(0, 20) + '...)' : 'No'
          });
          
          this.state.step = 'success';
          this.state.message = `Welcome to PastPort, ${registrationResult.authResult.username}!`;
          
          // Navigate to main app after short delay
          setTimeout(() => {
            console.log('🔄 Would navigate to dashboard (disabled for demo)');
            // this.router.navigate(['/dashboard']); // Disabled for frontend testing
          }, 2000);
        } else {
          // Registration successful but no authentication data
          this.state.step = 'success';
          this.state.message = `Welcome to PastPort, ${this.username}! Please try logging in.`;
          
          setTimeout(() => {
            console.log('🔄 Registration complete, redirecting to login');
            // Could redirect to login or retry authentication
          }, 2000);
        }
      } else {
        this.handleError('Failed to complete registration. Please try again.');
      }
    } catch (error) {
      console.error('Error completing registration:', error);
      this.handleError('Registration failed. Please try again.');
    } finally {
      this.state.isLoading = false;
    }
  }

  /**
   * Switch camera (front/back)
   */
  async switchCamera(): Promise<void> {
    try {
      this.facingMode = this.facingMode === 'user' ? 'environment' : 'user';
      await this.cameraService.switchCamera();
    } catch (error) {
      console.error('Error switching camera:', error);
    }
  }

  /**
   * Retry face recognition
   */
  retry(): void {
    this.state.step = 'camera';
    this.state.isLoading = false;
    this.state.showRetry = false;
    this.state.message = 'Position your face in the circle';
    
    this.startFaceDetection();
  }

  /**
   * Go back to regular login
   */
  goToRegularLogin(): void {
    this.router.navigate(['/auth/login']);
  }

  /**
   * Handle errors
   */
  private handleError(message: string): void {
    this.state.step = 'error';
    this.state.message = message;
    this.state.isLoading = false;
    this.state.showRetry = true;
    
    this.stopDetection();
  }

  /**
   * Stop face detection intervals
   */
  private stopDetection(): void {
    if (this.detectionInterval) {
      clearInterval(this.detectionInterval);
      this.detectionInterval = null;
    }
    
    if (this.livenessCheckInterval) {
      clearInterval(this.livenessCheckInterval);
      this.livenessCheckInterval = null;
    }
  }

  /**
   * Cleanup resources
   */
  private cleanup(): void {
    this.stopDetection();
    this.cameraService.stopCamera();
    
    // Unsubscribe from all subscriptions
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }
}
