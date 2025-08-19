export interface FaceDetectionResult {
  isDetected: boolean;
  confidence: number;
  landmarks?: any; // face-api.js FaceLandmarks68
  age?: number;
  gender?: string;
  expressions?: any; // face-api.js FaceExpressions
}

export interface LivenessResult {
  isLive: boolean;
  eyeBlinkDetected: boolean;
  headMovementDetected: boolean;
  textureAnalysis: boolean;
  confidence: number;
}

export interface FaceRecognitionResult {
  isRecognized: boolean;
  userId?: string;
  username?: string;
  confidence: number;
  ageGroup?: 'child' | 'teen' | 'adult' | 'senior';
}

export interface FaceEmbedding {
  descriptor: Float32Array;
  userId: string;
  username: string;
  createdAt: Date;
}

export interface AuthenticationResponse {
  status: 'success' | 'error';
  action: 'login' | 'register' | 'retry_liveness';
  user?: {
    id: string;
    name: string;
    age_group: 'child' | 'teen' | 'adult' | 'senior';
    email?: string;
  };
  token?: string;
  temp_face_id?: string;
  message: string;
  confidence?: number; // Face matching confidence from backend
}

export interface RegistrationRequest {
  temp_face_id: string;
  username: string;
}

export interface FaceLoginRequest {
  embeddings: number[][]; // List of 128-dimensional face embeddings
  device_info?: string;
}

export interface CameraConstraints {
  video: {
    facingMode: string;
    width: { ideal: number };
    height: { ideal: number };
  };
}

export interface ConsentData {
  hasConsented: boolean;
  consentDate: Date | null;
  consentVersion: string;
}

export interface BiometricConsentModal {
  title: string;
  content: string;
  acceptText: string;
  declineText: string;
}

export type AgeGroup = 'child' | 'teen' | 'adult' | 'senior';
export type AuthAction = 'login' | 'register' | 'retry_liveness';
export type AuthStatus = 'success' | 'error';
