export interface BackendUserResponse {
  user_id: string;
  email: string;
  username: string;
  age_group: string | null;
  auth_method: string;
  is_active: boolean;
  created_at: string;
}

export interface UserVerificationResult {
  isValid: boolean;
  userData: BackendUserResponse | null;
  discrepancies: string[];
  error?: string;
}

export interface UserComparisonResult {
  matches: boolean;
  differences: {
    field: string;
    localStorage: any;
    backend: any;
  }[];
}

export type UserVerificationStatus = 'success' | 'error' | 'mismatch' | 'network_error';
