import { Injectable } from '@angular/core';
import { BehaviorSubject, firstValueFrom } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import * as faceapi from 'face-api.js';
import { 
  FaceDetectionResult, 
  LivenessResult, 
  FaceRecognitionResult, 
  AgeGroup 
} from '../Models/face-recognition.models';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FaceLoginService {
  private modelsLoaded = false;
  private loadingSubject = new BehaviorSubject<boolean>(false);
  public loading$ = this.loadingSubject.asObservable();

  private readonly API_BASE_URL = `${environment.apiUrl}`;
  private readonly RECOGNITION_THRESHOLD = 0.4;

  // Liveness detection state
  private previousLandmarks: faceapi.FaceLandmarks68 | null = null;
  private blinkHistory: boolean[] = [];
  private headPositionHistory: number[] = [];
  private expressionHistory: any[] = [];

  // Store face data for registration after failed authentication
  private storedEmbedding: Float32Array | null = null;
  private storedFaceResult: FaceDetectionResult | null = null;
  private storedAgeGroup: AgeGroup | null = null;

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  /**
   * Load face-api.js models from public folder
   */
  async loadModels(): Promise<void> {
    if (this.modelsLoaded) return;

    this.loadingSubject.next(true);
    
    try {
      const MODEL_URL = '/models';
      console.log('Loading models from:', MODEL_URL);
      
      // Try to load SsdMobilenetv1 first, fallback to TinyFaceDetector if it fails
      try {
        await faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL);
        console.log('✅ SsdMobilenetv1 loaded successfully');
      } catch (ssdError) {
        console.warn('⚠️ SsdMobilenetv1 failed to load, falling back to TinyFaceDetector:', ssdError);
        await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
        console.log('✅ TinyFaceDetector loaded successfully');
      }
      
      await Promise.all([
        faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
        faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
        faceapi.nets.ageGenderNet.loadFromUri(MODEL_URL)
      ]);

      this.modelsLoaded = true;
      console.log('✅ All face-api.js models loaded successfully');
    } catch (error) {
      console.error('❌ Error loading face-api.js models:', error);
      throw new Error('Failed to load face recognition models');
    } finally {
      this.loadingSubject.next(false);
    }
  }

  /**
   * Detect face and extract features with fallback support
   */
  async detectFace(input: HTMLVideoElement | HTMLImageElement): Promise<FaceDetectionResult> {
    if (!this.modelsLoaded) {
      await this.loadModels();
    }

    try {
      console.log('🔍 Starting face detection...');
      
      if (!input) {
        console.error('❌ No input element provided');
        return { isDetected: false, confidence: 0 };
      }

      // For video elements, ensure they're ready
      if (input instanceof HTMLVideoElement) {
        if (input.readyState < 2) {
          console.log('⏳ Video not ready, waiting...');
          await new Promise(resolve => {
            const checkReady = () => {
              if (input.readyState >= 2) {
                resolve(void 0);
              } else {
                setTimeout(checkReady, 100);
              }
            };
            checkReady();
          });
        }

        if (input.videoWidth === 0 || input.videoHeight === 0) {
          console.log('❌ Video dimensions not available');
          return { isDetected: false, confidence: 0 };
        }
      }
      
      let detection;
      
      // Try SsdMobilenetv1 first, fallback to TinyFaceDetector
      if (faceapi.nets.ssdMobilenetv1.isLoaded) {
        console.log('📡 Using SsdMobilenetv1 for detection');
        detection = await faceapi
          .detectSingleFace(input, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.3 }))
          .withFaceLandmarks()
          .withFaceExpressions()
          .withAgeAndGender();
      } else if (faceapi.nets.tinyFaceDetector.isLoaded) {
        console.log('📡 Using TinyFaceDetector for detection');
        detection = await faceapi
          .detectSingleFace(input, new faceapi.TinyFaceDetectorOptions({ inputSize: 416, scoreThreshold: 0.3 }))
          .withFaceLandmarks()
          .withFaceExpressions()
          .withAgeAndGender();
      } else {
        throw new Error('No face detection models loaded');
      }

      if (!detection) {
        console.log('❌ No face detected');
        return {
          isDetected: false,
          confidence: 0
        };
      }

      console.log('✅ Face detected:', {
        confidence: detection.detection.score,
        age: detection.age,
        gender: detection.gender,
        hasLandmarks: !!detection.landmarks,
        hasExpressions: !!detection.expressions
      });

      return {
        isDetected: true,
        confidence: detection.detection.score,
        landmarks: detection.landmarks,
        age: detection.age,
        gender: detection.gender,
        expressions: detection.expressions
      };
    } catch (error) {
      console.error('❌ Error detecting face:', error);
      return {
        isDetected: false,
        confidence: 0
      };
    }
  }

  /**
   * Generate face embedding for recognition with fallback support
   */
  async generateFaceEmbedding(input: HTMLVideoElement | HTMLImageElement): Promise<Float32Array | null> {
    if (!this.modelsLoaded) {
      await this.loadModels();
    }

    try {
      console.log('🧬 Generating face embedding...');
      
      if (!input) {
        console.error('❌ No input element provided for embedding');
        return null;
      }

      // For video elements, ensure they're ready
      if (input instanceof HTMLVideoElement) {
        if (input.readyState < 2) {
          console.log('⏳ Video not ready for embedding, waiting...');
          await new Promise(resolve => {
            const checkReady = () => {
              if (input.readyState >= 2) {
                resolve(void 0);
              } else {
                setTimeout(checkReady, 100);
              }
            };
            checkReady();
          });
        }

        if (input.videoWidth === 0 || input.videoHeight === 0) {
          console.log('❌ Video dimensions not available for embedding');
          return null;
        }
      }
      
      let detection;
      
      // Try SsdMobilenetv1 first, fallback to TinyFaceDetector
      if (faceapi.nets.ssdMobilenetv1.isLoaded) {
        console.log('📡 Using SsdMobilenetv1 for embedding');
        detection = await faceapi
          .detectSingleFace(input, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.3 }))
          .withFaceLandmarks()
          .withFaceDescriptor();
      } else if (faceapi.nets.tinyFaceDetector.isLoaded) {
        console.log('📡 Using TinyFaceDetector for embedding');
        detection = await faceapi
          .detectSingleFace(input, new faceapi.TinyFaceDetectorOptions({ inputSize: 416, scoreThreshold: 0.3 }))
          .withFaceLandmarks()
          .withFaceDescriptor();
      } else {
        throw new Error('No face detection models loaded');
      }

      if (detection) {
        console.log('✅ Generated face descriptor:', {
          dimensions: detection.descriptor.length,
          confidence: detection.detection.score,
          hasLandmarks: !!detection.landmarks
        });
        return detection.descriptor;
      }
      
      console.log('❌ No face detected for embedding generation');
      return null;
    } catch (error) {
      console.error('❌ Error generating face embedding:', error);
      return null;
    }
  }

  /**
   * Convert face embedding to base64 string for backend transmission
   */
  private embeddingToBase64(embedding: Float32Array): string {
    const array = Array.from(embedding);
    return btoa(JSON.stringify(array));
  }

  /**
   * Perform liveness detection
   */
  async performLivenessDetection(input: HTMLVideoElement): Promise<LivenessResult> {
    const faceResult = await this.detectFace(input);
    
    if (!faceResult.isDetected || !faceResult.landmarks) {
      return {
        isLive: false,
        eyeBlinkDetected: false,
        headMovementDetected: false,
        textureAnalysis: false,
        confidence: 0
      };
    }

    // Eye blink detection
    const eyeBlinkDetected = this.detectEyeBlink(faceResult.landmarks);
    
    // Head movement detection
    const headMovementDetected = this.detectHeadMovement(faceResult.landmarks);
    
    // Basic texture analysis (check for expressions variation)
    const textureAnalysis = this.analyzeTexture(faceResult.expressions);

    const livenessScore = [eyeBlinkDetected, headMovementDetected, textureAnalysis]
      .filter(Boolean).length / 3;

    return {
      isLive: livenessScore >= 0.6, // At least 2 out of 3 checks must pass
      eyeBlinkDetected,
      headMovementDetected,
      textureAnalysis,
      confidence: livenessScore
    };
  }

  /**
   * Main authentication flow using backend matching
   */
  async authenticateUser(input: HTMLVideoElement): Promise<{
    isRecognized: boolean;
    isNewUser: boolean;
    userId?: string;
    username?: string;
    confidence?: number;
    ageGroup?: AgeGroup;
    requiresUsername?: boolean;
    accessToken?: string;
    refreshToken?: string;
    userData?: any;
  }> {
    try {
      console.log('🎯 Starting backend authentication flow...');
      
      // Step 1: Detect face and store the result for later use
      const faceResult = await this.detectFace(input);
      if (!faceResult.isDetected) {
        console.log('❌ No face detected');
        return {
          isRecognized: false,
          isNewUser: false,
          requiresUsername: false
        };
      }
      
      // Store face result and age group for potential registration
      this.storedFaceResult = faceResult;
      this.storedAgeGroup = this.determineAgeGroup(faceResult.age || 25);
      
      // Step 2: Generate face embedding
      const embedding = await this.generateFaceEmbedding(input);
      if (!embedding) {
        console.log('❌ No face embedding generated');
        return {
          isRecognized: false,
          isNewUser: false,
          requiresUsername: false
        };
      }

      // Step 3: Convert embedding to array for backend transmission
      const embeddingArray = [Array.from(embedding)];
      
      // Step 3: Send to backend API and transform response for AuthService
      try {
        console.log('📡 Sending face login request to backend...');
        const response = await firstValueFrom(
          this.http.post<any>(`${this.API_BASE_URL}/auth/face-login`, {
            embeddings: embeddingArray
          })
        );
        
        console.log('🔍 RAW BACKEND RESPONSE:', response);
        
        if (response.status === 'success' && response.access && response.data) {
          console.log('✅ Backend face authentication successful');
          
          // Transform backend response to match AuthenticationResponse interface
          const authResponse = {
            status: 'success' as const,
            action: 'login' as const,
            user: {
              id: response.data.user_id,
              name: response.data.username,
              age_group: response.data.age_group,
              email: response.data.email || undefined
            },
            token: response.access, // Use access token as the main token
            message: 'Face authentication successful',
            confidence: response.confidence
          };
          
          // Store refresh token separately (the interceptor looks for it)
          if (response.refresh) {
            localStorage.setItem('pastport_refresh_token', response.refresh);
          }
          
          // Let AuthService handle the token and user data storage properly
          await this.authService.handleSuccessfulLogin(authResponse);
          
          // Clear stored face data for security after successful authentication
          this.clearStoredFaceData();
          
          return {
            isRecognized: true,
            isNewUser: false,
            userId: response.data.user_id,
            username: response.data.username,
            confidence: response.confidence || 0.8,
            ageGroup: response.data.age_group,
            requiresUsername: false,
            accessToken: response.access,
            refreshToken: response.refresh,
            userData: response.data
          };
        }
      } catch (error: any) {
        console.log('🔍 Face not recognized by backend, checking if new user...', error);
        
        // Check if this is a "Face not recognized" error (new user scenario)
        if (error.error?.detail === 'Face not recognized' || 
            error.status === 401 || 
            error.error?.message?.includes('not found') || 
            error.error?.message?.includes('No matching')) {
          
          console.log('👤 Face not recognized - treating as new user');
          
          // Store the embedding for later registration
          this.storedEmbedding = embedding;
          // Use the age group we already detected and stored
          const ageGroup = this.storedAgeGroup || 'adult';
          
          console.log('💾 Stored embedding for registration:', {
            embeddingDimensions: embedding.length,
            ageGroup: ageGroup
          });
          
          return {
            isRecognized: false,
            isNewUser: true,
            ageGroup: ageGroup,
            requiresUsername: true
          };
        }
        
        // Other errors (network issues, server errors, etc.)
        console.error('❌ Unexpected error during face authentication:', error);
        // Clear stored face data for security on authentication errors
        this.clearStoredFaceData();
        throw error;
      }
      
      return {
        isRecognized: false,
        isNewUser: false,
        requiresUsername: false
      };
      
    } catch (error) {
      console.error('❌ Error in backend authentication flow:', error);
      return {
        isRecognized: false,
        isNewUser: false,
        requiresUsername: false
      };
    }
  }

  /**
   * Register new user with backend and handle authentication
   */
  async registerNewUser(input: HTMLVideoElement | null, username: string): Promise<{
    success: boolean;
    authResult?: {
      isRecognized: boolean;
      isNewUser: boolean;
      userId?: string;
      username?: string;
      confidence?: number;
      ageGroup?: AgeGroup;
      requiresUsername?: boolean;
      accessToken?: string;
      refreshToken?: string;
      userData?: any;
    };
  }> {
    try {
      console.log('📝 Registering new user with backend:', username);
      
      // Use stored embedding from failed authentication
      if (!this.storedEmbedding) {
        console.error('❌ No stored face embedding available for registration');
        return { success: false };
      }

      const embedding = this.storedEmbedding;
      const ageGroup = this.storedAgeGroup || 'adult';

      console.log('💾 Using stored embedding for registration:', {
        embeddingDimensions: embedding.length,
        ageGroup: ageGroup
      });

      // Convert embedding to array format for backend
      const embeddingArray = [Array.from(embedding)];
      
      // Send to backend for registration
      const response = await firstValueFrom(
        this.http.post<any>(`${this.API_BASE_URL}/auth/face-register`, {
          embeddings: embeddingArray,
          username: username,
          age_group: ageGroup
        })
      );
      
      console.log('🔍 REGISTRATION RESPONSE:', response);
      
      if (response.status === 'success') {
        console.log('✅ New user registered with backend successfully');
        
        // Check if the backend returns authentication tokens after registration
        if (response.access && response.data) {
          console.log('🔑 Registration included authentication tokens');
          
          // Transform response for AuthService
          const authResponse = {
            status: 'success' as const,
            action: 'login' as const,
            user: {
              id: response.data.user_id,
              name: response.data.username,
              age_group: response.data.age_group,
              email: response.data.email || undefined
            },
            token: response.access,
            message: 'Registration and authentication successful',
            confidence: response.confidence
          };
          
          // Store refresh token separately
          if (response.refresh) {
            localStorage.setItem('pastport_refresh_token', response.refresh);
          }
          
          // Let AuthService handle the token and user data storage
          await this.authService.handleSuccessfulLogin(authResponse);
          
          // Clear stored face data for security after successful registration
          this.clearStoredFaceData();
          
          return {
            success: true,
            authResult: {
              isRecognized: true,
              isNewUser: false, // Now they're registered
              userId: response.data.user_id,
              username: response.data.username,
              confidence: response.confidence || 0.8,
              ageGroup: response.data.age_group,
              requiresUsername: false,
              accessToken: response.access,
              refreshToken: response.refresh,
              userData: response.data
            }
          };
        } else {
          // Registration successful but no auth tokens
          console.log('📝 Registration successful but no authentication tokens returned');
          
          // Return success without authentication data
          return {
            success: true,
            authResult: {
              isRecognized: true,
              isNewUser: false, // Now they're registered
              userId: response.data?.user_id,
              username: response.data?.username || username,
              confidence: 0.8,
              ageGroup: ageGroup,
              requiresUsername: false
            }
          };
        }
      }
      
      // Clear stored face data for security after failed registration
      this.clearStoredFaceData();
      return { success: false };
    } catch (error) {
      console.error('❌ Error registering new user with backend:', error);
      // Clear stored face data for security on registration errors
      this.clearStoredFaceData();
      return { success: false };
    }
  }

  /**
   * Determine age group from detected age
   */
  private determineAgeGroup(age: number): AgeGroup {
    if (age <= 12) return 'child';
    if (age <= 17) return 'teen';
    if (age <= 64) return 'adult';
    return 'senior';
  }

  /**
   * Detect eye blink based on eye aspect ratio
   */
  private detectEyeBlink(landmarks: faceapi.FaceLandmarks68): boolean {
    const leftEye = landmarks.getLeftEye();
    const rightEye = landmarks.getRightEye();
    
    const leftEAR = this.calculateEyeAspectRatio(leftEye);
    const rightEAR = this.calculateEyeAspectRatio(rightEye);
    
    const avgEAR = (leftEAR + rightEAR) / 2;
    const isBlinking = avgEAR < 0.25; // Threshold for blink detection
    
    // Store blink history
    this.blinkHistory.push(isBlinking);
    if (this.blinkHistory.length > 10) {
      this.blinkHistory.shift();
    }
    
    // Check if there was a blink in recent history
    return this.blinkHistory.some(blink => blink);
  }

  /**
   * Calculate Eye Aspect Ratio for blink detection
   */
  private calculateEyeAspectRatio(eyePoints: faceapi.Point[]): number {
    if (eyePoints.length < 6) return 0;
    
    const vertical1 = Math.sqrt(
      Math.pow(eyePoints[1].x - eyePoints[5].x, 2) + 
      Math.pow(eyePoints[1].y - eyePoints[5].y, 2)
    );
    
    const vertical2 = Math.sqrt(
      Math.pow(eyePoints[2].x - eyePoints[4].x, 2) + 
      Math.pow(eyePoints[2].y - eyePoints[4].y, 2)
    );
    
    const horizontal = Math.sqrt(
      Math.pow(eyePoints[0].x - eyePoints[3].x, 2) + 
      Math.pow(eyePoints[0].y - eyePoints[3].y, 2)
    );
    
    return (vertical1 + vertical2) / (2 * horizontal);
  }

  /**
   * Detect head movement
   */
  private detectHeadMovement(landmarks: faceapi.FaceLandmarks68): boolean {
    const nose = landmarks.getNose()[3]; // Nose tip
    const currentPosition = nose.x + nose.y; // Simple position metric
    
    this.headPositionHistory.push(currentPosition);
    if (this.headPositionHistory.length > 5) {
      this.headPositionHistory.shift();
    }
    
    if (this.headPositionHistory.length < 3) return false;
    
    // Check for significant position changes
    const maxPos = Math.max(...this.headPositionHistory);
    const minPos = Math.min(...this.headPositionHistory);
    const movement = maxPos - minPos;
    
    return movement > 20; // Threshold for head movement
  }

  /**
   * Analyze texture/expression variation for liveness detection
   */
  private analyzeTexture(expressions: any): boolean {
    if (!expressions) return false;
    
    // Store expression history for analysis
    this.expressionHistory.push(expressions);
    if (this.expressionHistory.length > 5) {
      this.expressionHistory.shift();
    }
    
    if (this.expressionHistory.length < 3) return false;
    
    // Check for variation in expressions (indicates natural facial movement)
    const expressionKeys = ['neutral', 'happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised'];
    let hasVariation = false;
    
    for (const key of expressionKeys) {
      const values = this.expressionHistory.map(exp => exp[key] || 0);
      const max = Math.max(...values);
      const min = Math.min(...values);
      
      // If there's significant variation in any expression, consider it natural
      if (max - min > 0.1) {
        hasVariation = true;
        break;
      }
    }
    
    return hasVariation;
  }

  /**
   * Check if models are loaded
   */
  areModelsLoaded(): boolean {
    return this.modelsLoaded;
  }

  /**
   * Clear stored face data for security
   */
  private clearStoredFaceData(): void {
    this.storedEmbedding = null;
    this.storedFaceResult = null;
    this.storedAgeGroup = null;
    console.log('🧹 Cleared stored face data for security');
  }

  /**
   * Clear authentication state (for testing)
   */
  clearAuthData(): void {
    this.authService.clearAllAuthData();
    this.clearStoredFaceData();
    console.log('🧹 Cleared all authentication data');
  }

  /**
   * Get stored embeddings count (now from backend)
   */
  async getStoredEmbeddingsCount(): Promise<number> {
    try {
      const response = await firstValueFrom(
        this.http.get<any>(`${this.API_BASE_URL}/auth/users/count`)
      );
      return response.count || 0;
    } catch (error) {
      console.error('Error getting stored embeddings count:', error);
      return 0;
    }
  }
}
