import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import * as faceapi from 'face-api.js';
import { 
  FaceDetectionResult, 
  LivenessResult, 
  FaceRecognitionResult, 
  FaceEmbedding,
  AgeGroup 
} from '../Models/face-recognition.models';

// Enhanced user profile for mock database with multiple embeddings
interface UserProfile {
  id: string;
  username: string;
  featureVectors: Float32Array[]; // Multiple embeddings for better accuracy
  age: number;
  gender: string;
  ageGroup: AgeGroup;
  createdAt: string;
  lastLogin?: string;
}

// Temporary face data interface
interface TempFaceData {
  embeddings: Float32Array[];
  ageGroup: AgeGroup;
  age: number;
  gender: string;
}

@Injectable({
  providedIn: 'root'
})
export class FaceLoginService {
  private modelsLoaded = false;
  private loadingSubject = new BehaviorSubject<boolean>(false);
  public loading$ = this.loadingSubject.asObservable();

  // Enhanced mock database
  private userProfiles: UserProfile[] = [];
  private faceMatcher: faceapi.FaceMatcher | null = null;
  private readonly DATABASE_FILE_PATH = '/assets/pastport_face_database.json';
  private readonly DATABASE_FILE = 'pastport_face_database.json';
  private readonly RECOGNITION_THRESHOLD = 0.4; // Lower = more strict (distance threshold)

  // Temporary face data storage
  private tempFaceData = new Map<string, TempFaceData>();

  // Liveness detection state
  private previousLandmarks: faceapi.FaceLandmarks68 | null = null;
  private blinkHistory: boolean[] = [];
  private headPositionHistory: number[] = [];
  private expressionHistory: any[] = [];

  constructor() {
    this.loadFromAssetFile();
  }

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
      console.log('📊 Model status:', {
        ssdMobilenetv1: faceapi.nets.ssdMobilenetv1.isLoaded,
        tinyFaceDetector: faceapi.nets.tinyFaceDetector.isLoaded,
        faceLandmark68: faceapi.nets.faceLandmark68Net.isLoaded,
        faceRecognition: faceapi.nets.faceRecognitionNet.isLoaded,
        faceExpression: faceapi.nets.faceExpressionNet.isLoaded,
        ageGender: faceapi.nets.ageGenderNet.isLoaded
      });
      
      // Initialize FaceMatcher if we have stored profiles
      this.initializeFaceMatcher();
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
      
      // Validate input element
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
   * Generate face embedding for recognition with fallback support
   */
  async generateFaceEmbedding(input: HTMLVideoElement | HTMLImageElement): Promise<Float32Array | null> {
    if (!this.modelsLoaded) {
      await this.loadModels();
    }

    try {
      console.log('🧬 Generating face embedding...');
      
      // Validate input element
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
   * Recognize face using FaceMatcher for better accuracy
   */
  async recognizeFace(input: HTMLVideoElement | HTMLImageElement): Promise<FaceRecognitionResult> {
    const embedding = await this.generateFaceEmbedding(input);
    
    if (!embedding || this.userProfiles.length === 0 || !this.faceMatcher) {
      console.log('No embedding generated or no stored profiles or FaceMatcher not initialized');
      return {
        isRecognized: false,
        confidence: 0
      };
    }

    try {
      // Use FaceMatcher to find best match
      const bestMatch = this.faceMatcher.findBestMatch(embedding);
      console.log('FaceMatcher result:', bestMatch);
      
      const isRecognized = bestMatch.label !== 'unknown' && bestMatch.distance < this.RECOGNITION_THRESHOLD;
      
      if (isRecognized) {
        // Find the user profile by label (username)
        const userProfile = this.userProfiles.find(profile => profile.username === bestMatch.label);
        
        if (userProfile) {
          // Get current age group (might have changed since registration)
          const faceResult = await this.detectFace(input);
          const currentAgeGroup = this.determineAgeGroup(faceResult.age || userProfile.age);

          return {
            isRecognized: true,
            userId: userProfile.id,
            username: userProfile.username,
            confidence: 1 - bestMatch.distance, // Convert distance to confidence
            ageGroup: currentAgeGroup
          };
        }
      }

      return {
        isRecognized: false,
        confidence: 0
      };
    } catch (error) {
      console.error('Error in face recognition:', error);
      return {
        isRecognized: false,
        confidence: 0
      };
    }
  }

  /**
   * Store multiple face embeddings for new user with enhanced profile data
   */
  async storeMultipleEmbeddings(embeddings: Float32Array[], userId: string, username: string): Promise<boolean> {
    if (!embeddings || embeddings.length === 0) {
      console.error('No embeddings provided for storage');
      return false;
    }

    console.log('📦 Storing multiple embeddings:', {
      count: embeddings.length,
      dimensions: embeddings[0].length,
      userId,
      username
    });

    // Use the first embedding to get age and gender (they should be consistent)
    const userProfile: UserProfile = {
      id: userId,
      username,
      featureVectors: embeddings, // Store all embeddings
      age: 25, // Default age, will be updated during recognition
      gender: 'unknown', // Default gender
      ageGroup: this.determineAgeGroup(25),
      createdAt: new Date().toISOString()
    };

    this.userProfiles.push(userProfile);
    await this.saveProfilesToStorage();
    
    // Reinitialize FaceMatcher with new profile
    this.initializeFaceMatcher();
    
    console.log('✅ Stored new user profile with multiple embeddings:', { 
      userId, 
      username, 
      embeddingCount: embeddings.length,
      totalProfiles: this.userProfiles.length
    });
    return true;
  }

  /**
   * Store face embedding for new user (legacy method for backward compatibility)
   */
  async storeFaceEmbedding(input: HTMLVideoElement | HTMLImageElement, userId: string, username: string): Promise<boolean> {
    const embedding = await this.generateFaceEmbedding(input);
    
    if (!embedding) {
      console.error('Failed to generate face embedding');
      return false;
    }

    // Get age and gender information
    const faceResult = await this.detectFace(input);
    const age = faceResult.age || 25;
    const gender = faceResult.gender || 'unknown';
    const ageGroup = this.determineAgeGroup(age);

    const userProfile: UserProfile = {
      id: userId,
      username,
      featureVectors: [embedding], // Store as array for consistency
      age,
      gender,
      ageGroup,
      createdAt: new Date().toISOString()
    };

    this.userProfiles.push(userProfile);
    await this.saveProfilesToStorage();
    
    // Reinitialize FaceMatcher with new profile
    this.initializeFaceMatcher();
    
    console.log('✅ Stored new user profile:', { userId, username, age, gender, ageGroup });
    return true;
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
   * Recognize face using multiple embeddings for better accuracy
   */
  async recognizeMultipleEmbeddings(embeddings: Float32Array[]): Promise<FaceRecognitionResult> {
    if (!embeddings || embeddings.length === 0 || this.userProfiles.length === 0 || !this.faceMatcher) {
      console.log('❌ No embeddings provided or no stored profiles or FaceMatcher not initialized');
      return {
        isRecognized: false,
        confidence: 0
      };
    }

    try {
      console.log('🔍 Recognizing using multiple embeddings:', {
        embeddingCount: embeddings.length,
        storedProfiles: this.userProfiles.length
      });

      let bestOverallMatch: any = null;
      let bestOverallConfidence = 0;
      let bestProfile: UserProfile | null = null;

      // Test each embedding against all stored profiles
      for (const embedding of embeddings) {
        const match = this.faceMatcher.findBestMatch(embedding);
        const confidence = 1 - match.distance;
        
        console.log('🎯 Embedding match result:', {
          label: match.label,
          distance: match.distance,
          confidence: confidence
        });

        if (match.label !== 'unknown' && confidence > bestOverallConfidence && match.distance < this.RECOGNITION_THRESHOLD) {
          bestOverallMatch = match;
          bestOverallConfidence = confidence;
          bestProfile = this.userProfiles.find(profile => profile.username === match.label) || null;
        }
      }

      if (bestOverallMatch && bestProfile && bestOverallConfidence > 0) {
        console.log('✅ Multi-embedding recognition successful:', {
          username: bestProfile.username,
          confidence: bestOverallConfidence,
          embeddingsUsed: embeddings.length
        });

        return {
          isRecognized: true,
          userId: bestProfile.id,
          username: bestProfile.username,
          confidence: bestOverallConfidence,
          ageGroup: bestProfile.ageGroup
        };
      }

      console.log('❌ No match found with multiple embeddings');
      return {
        isRecognized: false,
        confidence: 0
      };
    } catch (error) {
      console.error('❌ Error in multi-embedding recognition:', error);
      return {
        isRecognized: false,
        confidence: 0
      };
    }
  }

  /**
   * Initialize FaceMatcher with stored user profiles (supporting multiple embeddings)
   */
  private initializeFaceMatcher(): void {
    if (this.userProfiles.length === 0) {
      this.faceMatcher = null;
      return;
    }

    try {
      // Create labeled face descriptors for FaceMatcher using all embeddings
      const labeledDescriptors = this.userProfiles.map(profile => 
        new faceapi.LabeledFaceDescriptors(profile.username, profile.featureVectors)
      );

      this.faceMatcher = new faceapi.FaceMatcher(labeledDescriptors, this.RECOGNITION_THRESHOLD);
      
      const totalEmbeddings = this.userProfiles.reduce((sum, profile) => sum + profile.featureVectors.length, 0);
      console.log('✅ FaceMatcher initialized:', {
        profiles: this.userProfiles.length,
        totalEmbeddings: totalEmbeddings,
        threshold: this.RECOGNITION_THRESHOLD
      });
    } catch (error) {
      console.error('❌ Error initializing FaceMatcher:', error);
      this.faceMatcher = null;
    }
  }

  /**
   * Load stored user profiles from assets file (supporting multiple embeddings)
   */
  private async loadStoredProfiles(): Promise<void> {
    try {
      console.log('📂 Loading user profiles from assets file...');
      
      const response = await fetch(this.DATABASE_FILE_PATH);
      
      if (!response.ok) {
        console.log('📂 No asset database file found, starting with empty database');
        this.userProfiles = [];
        return;
      }
      
      const data = await response.json();
      
      if (data.profiles && Array.isArray(data.profiles)) {
        this.userProfiles = data.profiles.map((item: any) => ({
          ...item,
          // Handle both old single embedding and new multiple embeddings format
          featureVectors: item.featureVectors 
            ? item.featureVectors.map((vec: number[]) => new Float32Array(vec))
            : [new Float32Array(item.featureVector)], // Convert old format
          createdAt: item.createdAt // Keep as string
        }));
        
        const totalEmbeddings = this.userProfiles.reduce((sum, profile) => sum + profile.featureVectors.length, 0);
        console.log('✅ Loaded user profiles from assets file:', {
          profiles: this.userProfiles.length,
          totalEmbeddings: totalEmbeddings
        });
        
        // Initialize FaceMatcher after loading profiles
        this.initializeFaceMatcher();
      } else {
        console.log('📂 Asset file exists but contains no profiles');
        this.userProfiles = [];
      }
    } catch (error) {
      console.log('📂 Could not load from asset file (starting with empty database):', error);
      this.userProfiles = [];
    }
  }

  /**
   * Save user profiles to assets file (supporting multiple embeddings)
   */
  private async saveProfilesToStorage(): Promise<void> {
    try {
      const dataToExport = {
        version: '1.0',
        timestamp: new Date().toISOString(),
        profiles: this.userProfiles.map(profile => ({
          ...profile,
          featureVectors: profile.featureVectors.map(vec => Array.from(vec))
        }))
      };
      
      const jsonString = JSON.stringify(dataToExport, null, 2);
      
      // Force download the updated file
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = this.DATABASE_FILE;
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      
      setTimeout(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }, 100);
      
      const totalEmbeddings = this.userProfiles.reduce((sum, profile) => sum + profile.featureVectors.length, 0);
      console.log('💾 Saved user profiles to file:', {
        profiles: this.userProfiles.length,
        totalEmbeddings: totalEmbeddings,
        filename: this.DATABASE_FILE
      });
    } catch (error) {
      console.error('❌ Error saving profiles to file:', error);
    }
  }


  /**
   * Load face database from assets file (primary data source)
   */
  private async loadFromAssetFile(): Promise<void> {
    await this.loadStoredProfiles();
  }

  /**
   * Manually trigger database file download (for testing)
   */
  public downloadDatabaseFile(): void {
    console.log('🔄 Manually triggering database download...');
    this.saveProfilesToStorage();
  }

  /**
   * Complete new user registration using temporary face data (no video element needed)
   */
  async completeNewUserRegistrationWithId(tempFaceId: string, username: string): Promise<boolean> {
    try {
      console.log('🔄 COMPLETING REGISTRATION WITH TEMP ID:', { tempFaceId, username });
      
      // Check if we have temporary face data stored
      const tempData = this.tempFaceData.get(tempFaceId);
      if (!tempData) {
        console.error('❌ No temporary face data found for ID:', tempFaceId);
        
        // Fallback: capture fresh embeddings directly
        console.log('🔄 Fallback: capturing fresh embeddings for registration...');
        return await this.completeNewUserRegistration(null as any, username);
      }

      // Create user profile from temporary data
      const userProfile: UserProfile = {
        id: `user_${Date.now()}`,
        username: username,
        featureVectors: tempData.embeddings,
        age: tempData.age,
        gender: tempData.gender,
        ageGroup: tempData.ageGroup,
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString()
      };

      // Store the profile
      this.userProfiles.push(userProfile);
      
      // Clean up temporary data
      this.tempFaceData.delete(tempFaceId);
      
      // Save to storage
      await this.saveProfilesToStorage();

      console.log('✅ NEW USER REGISTERED FROM TEMP DATA:', {
        id: userProfile.id,
        username: userProfile.username,
        embeddingCount: userProfile.featureVectors.length,
        ageGroup: userProfile.ageGroup
      });

      return true;
    } catch (error) {
      console.error('❌ Error completing registration with temp ID:', error);
      return false;
    }
  }

  /**
   * Clear all stored user profiles
   */
  async clearStoredEmbeddings(): Promise<void> {
    this.userProfiles = [];
    this.faceMatcher = null;
    
    // Save empty database to file
    await this.saveProfilesToStorage();
    
    console.log('Cleared all stored user profiles and saved empty database file');
  }

  /**
   * Get number of stored user profiles
   */
  getStoredEmbeddingsCount(): number {
    return this.userProfiles.length;
  }

  /**
   * Check if models are loaded
   */
  areModelsLoaded(): boolean {
    return this.modelsLoaded;
  }

  /**
   * Main authentication flow: Capture 3 images, try to match, auto-register if no match
   */
  async authenticateUser(input: HTMLVideoElement): Promise<{
    isRecognized: boolean;
    isNewUser: boolean;
    userId?: string;
    username?: string;
    confidence?: number;
    ageGroup?: AgeGroup;
    requiresUsername?: boolean;
  }> {
    try {
      console.log('🎯 Starting authentication flow...');
      
      // Step 1: Capture 3 face embeddings
      const embeddings: Float32Array[] = [];
      const captureDelay = 500; // 500ms between captures
      
      for (let i = 0; i < 3; i++) {
        console.log(`📸 Capturing embedding ${i + 1}/3...`);
        
        const embedding = await this.generateFaceEmbedding(input);
        if (embedding) {
          embeddings.push(embedding);
          console.log(`✅ Captured embedding ${i + 1}: ${embedding.length} dimensions`);
        } else {
          console.log(`❌ Failed to capture embedding ${i + 1}`);
        }
        
        // Wait between captures (except for the last one)
        if (i < 2) {
          await new Promise(resolve => setTimeout(resolve, captureDelay));
        }
      }
      
      if (embeddings.length === 0) {
        console.log('❌ No face embeddings captured');
        return {
          isRecognized: false,
          isNewUser: false,
          requiresUsername: false
        };
      }
      
      console.log(`📦 Captured ${embeddings.length} embeddings for authentication`);
      
      // Step 2: Try to recognize using captured embeddings
      if (this.userProfiles.length > 0 && this.faceMatcher) {
        console.log('🔍 Attempting recognition with existing database...');
        const recognitionResult = await this.recognizeMultipleEmbeddings(embeddings);
        
        if (recognitionResult.isRecognized) {
          console.log('✅ User recognized!');
          return {
            isRecognized: true,
            isNewUser: false,
            userId: recognitionResult.userId,
            username: recognitionResult.username,
            confidence: recognitionResult.confidence,
            ageGroup: recognitionResult.ageGroup,
            requiresUsername: false
          };
        }
      }
      
      // Step 3: No match found or empty database - auto-register as new user
      console.log('👤 No match found, registering as new user...');
      
      // Get additional face data from the first successful capture
      const faceResult = await this.detectFace(input);
      const age = faceResult.age || 25;
      const gender = faceResult.gender || 'unknown';
      const ageGroup = this.determineAgeGroup(age);
      
      // Generate a temporary user ID
      const tempUserId = `user_${Date.now()}`;
      
      // Store the captured embeddings temporarily for registration
      const tempData: TempFaceData = {
        embeddings: embeddings,
        ageGroup: ageGroup,
        age: age,
        gender: gender
      };
      
      this.tempFaceData.set(tempUserId, tempData);
      
      console.log('💾 Stored temporary face data:', {
        tempUserId,
        embeddingCount: embeddings.length,
        ageGroup,
        age,
        gender
      });
      
      // For now, we'll need to ask for username, but we can auto-register with embeddings
      return {
        isRecognized: false,
        isNewUser: true,
        userId: tempUserId,
        ageGroup: ageGroup,
        requiresUsername: true, // Component should ask for username then call completeNewUserRegistrationWithId
        confidence: 0
      };
      
    } catch (error) {
      console.error('❌ Error in authentication flow:', error);
      return {
        isRecognized: false,
        isNewUser: false,
        requiresUsername: false
      };
    }
  }

  /**
   * Complete new user registration with username (called after authenticateUser returns requiresUsername: true)
   */
  async completeNewUserRegistration(input: HTMLVideoElement, username: string): Promise<boolean> {
    try {
      console.log('📝 Completing new user registration for:', username);
      
      // Capture fresh embeddings for registration
      const embeddings: Float32Array[] = [];
      const captureDelay = 500;
      
      for (let i = 0; i < 3; i++) {
        const embedding = await this.generateFaceEmbedding(input);
        if (embedding) {
          embeddings.push(embedding);
        }
        if (i < 2) {
          await new Promise(resolve => setTimeout(resolve, captureDelay));
        }
      }
      
      if (embeddings.length === 0) {
        console.error('❌ Failed to capture embeddings for registration');
        return false;
      }
      
      // Generate proper user ID
      const userId = `user_${username}_${Date.now()}`;
      
      // Store the new user with multiple embeddings
      const success = await this.storeMultipleEmbeddings(embeddings, userId, username);
      
      if (success) {
        console.log('✅ New user registration completed successfully');
        return true;
      } else {
        console.error('❌ Failed to store new user embeddings');
        return false;
      }
      
    } catch (error) {
      console.error('❌ Error completing new user registration:', error);
      return false;
    }
  }
}
