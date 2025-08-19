"""
Pydantic schemas for authentication endpoints
Defines request/response models for JWT authentication
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Request schemas
class LoginRequest(BaseModel):
    """Email/password login request"""
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """Traditional email/password registration request"""
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)


class FaceLoginRequest(BaseModel):
    """Face recognition login request"""
    embeddings: List[List[float]] = Field(..., description="List of 128-dimensional face embeddings")


class FaceRegisterRequest(BaseModel):
    """Face registration request for new users"""
    username: str = Field(..., min_length=2, max_length=100)
    embeddings: List[List[float]] = Field(..., description="List of 128-dimensional face embeddings")
    age_group: Optional[str] = Field(None, description="Age group: child, teen, adult, senior")


class LinkFaceRequest(BaseModel):
    """Link face authentication to existing email account"""
    embeddings: List[List[float]] = Field(..., description="List of 128-dimensional face embeddings")
    age_group: Optional[str] = Field(None, description="Age group: child, teen, adult, senior")


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh: str = Field(..., description="Refresh token")


class LogoutRequest(BaseModel):
    """Logout request"""
    refresh: str = Field(..., description="Refresh token to blacklist")


# Response schemas
class UserData(BaseModel):
    """User data included in token responses"""
    user_id: str
    email: Optional[str]
    username: str
    age_group: Optional[str]
    auth_method: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response (matching Django SimpleJWT format)"""
    access: str = Field(..., description="Access token")
    refresh: str = Field(..., description="Refresh token")
    status: str = Field(default="success", description="Response status")
    data: UserData = Field(..., description="User data")
    confidence: Optional[float] = Field(None, description="Face matching confidence (for face login)")


class RefreshResponse(BaseModel):
    """Token refresh response"""
    access: str = Field(..., description="New access token")
    status: str = Field(default="success", description="Response status")


class FaceMatchResponse(BaseModel):
    """Face matching service response"""
    matched: bool = Field(..., description="Whether a match was found")
    user_id: Optional[str] = Field(None, description="Matched user ID")
    confidence: float = Field(..., description="Match confidence (0-1)")
    distance: Optional[float] = Field(None, description="Euclidean distance")


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    status: str = Field(default="success")


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    status: str = Field(default="error")


# Internal schemas for face matching
class FaceMatchRequest(BaseModel):
    """Internal face matching request"""
    embeddings: List[List[float]] = Field(..., description="Face embeddings to match")
    
    class Config:
        schema_extra = {
            "example": {
                "embeddings": [
                    [0.1, 0.2, 0.3],  # Truncated for example
                    [0.4, 0.5, 0.6],
                    [0.7, 0.8, 0.9]
                ]
            }
        }


class UserProfileUpdate(BaseModel):
    """User profile update request"""
    username: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com"
            }
        }


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="Email address for password reset")


# Validation schemas
class EmbeddingValidation(BaseModel):
    """Embedding validation response"""
    valid: bool
    dimension: Optional[int] = None
    error_message: Optional[str] = None


class AuthMethodInfo(BaseModel):
    """Authentication method information"""
    has_email: bool
    has_face: bool
    auth_method: str
    can_add_email: bool
    can_add_face: bool
