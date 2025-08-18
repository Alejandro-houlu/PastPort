import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface ConsentData {
  hasConsented: boolean;
  consentDate: Date | null;
  consentVersion: string;
}

@Injectable({
  providedIn: 'root'
})
export class BiometricConsentService {
  private readonly CONSENT_STORAGE_KEY = 'pastport_biometric_consent';
  private readonly CURRENT_CONSENT_VERSION = '1.0';
  
  private consentSubject = new BehaviorSubject<ConsentData>(this.loadConsentData());
  public consent$ = this.consentSubject.asObservable();

  constructor() { }

  /**
   * Load consent data from localStorage
   */
  private loadConsentData(): ConsentData {
    try {
      const stored = localStorage.getItem(this.CONSENT_STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        return {
          hasConsented: data.hasConsented || false,
          consentDate: data.consentDate ? new Date(data.consentDate) : null,
          consentVersion: data.consentVersion || '1.0'
        };
      }
    } catch (error) {
      console.error('Error loading consent data:', error);
    }
    
    return {
      hasConsented: false,
      consentDate: null,
      consentVersion: this.CURRENT_CONSENT_VERSION
    };
  }

  /**
   * Save consent data to localStorage
   */
  private saveConsentData(data: ConsentData): void {
    try {
      localStorage.setItem(this.CONSENT_STORAGE_KEY, JSON.stringify(data));
      this.consentSubject.next(data);
    } catch (error) {
      console.error('Error saving consent data:', error);
    }
  }

  /**
   * Grant biometric consent
   */
  grantConsent(): void {
    const consentData: ConsentData = {
      hasConsented: true,
      consentDate: new Date(),
      consentVersion: this.CURRENT_CONSENT_VERSION
    };
    this.saveConsentData(consentData);
  }

  /**
   * Revoke biometric consent
   */
  revokeConsent(): void {
    const consentData: ConsentData = {
      hasConsented: false,
      consentDate: null,
      consentVersion: this.CURRENT_CONSENT_VERSION
    };
    this.saveConsentData(consentData);
    
    // Clear any stored biometric data
    this.clearBiometricData();
  }

  /**
   * Check if user has granted consent
   */
  hasValidConsent(): boolean {
    const data = this.consentSubject.value;
    return data.hasConsented && data.consentVersion === this.CURRENT_CONSENT_VERSION;
  }

  /**
   * Get current consent data
   */
  getConsentData(): ConsentData {
    return this.consentSubject.value;
  }

  /**
   * Check if consent is required (new version or no consent)
   */
  isConsentRequired(): boolean {
    const data = this.consentSubject.value;
    return !data.hasConsented || data.consentVersion !== this.CURRENT_CONSENT_VERSION;
  }

  /**
   * Clear stored biometric data
   */
  private clearBiometricData(): void {
    try {
      // Remove any stored face embeddings or biometric data
      localStorage.removeItem('pastport_face_embeddings');
      localStorage.removeItem('pastport_user_biometric_data');
    } catch (error) {
      console.error('Error clearing biometric data:', error);
    }
  }

  /**
   * Get consent modal content
   */
  getConsentModalContent(): {
    title: string;
    content: string;
    acceptText: string;
    declineText: string;
  } {
    return {
      title: 'Biometric Authentication Consent',
      content: `
        PastPort uses facial recognition technology to provide secure and convenient authentication.
        
        By consenting, you agree that:
        • Your facial features will be analyzed and converted to an encrypted mathematical template
        • No actual photos of your face will be stored
        • Your biometric data will be encrypted and stored securely
        • You can revoke this consent at any time in your account settings
        • This data will only be used for authentication purposes
        
        Your privacy and security are our top priorities. All biometric processing happens locally on your device, and only encrypted templates are transmitted to our servers.
      `,
      acceptText: 'I Consent',
      declineText: 'Use Email/Password Instead'
    };
  }

  /**
   * Reset consent (for testing purposes)
   */
  resetConsent(): void {
    localStorage.removeItem(this.CONSENT_STORAGE_KEY);
    this.consentSubject.next(this.loadConsentData());
  }
}
