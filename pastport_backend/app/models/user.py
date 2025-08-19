"""
User model for PastPort authentication system
Supports both email/password and face recognition authentication
"""
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text
from passlib.context import CryptContext

from ..database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"
    
    # Primary key - UUID for unique identification
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Traditional auth fields
    email = Column(String(255), unique=True, index=True, nullable=True)  # Nullable for face-only users
    hashed_password = Column(String(255), nullable=True)  # Nullable for face-only users
    
    # Face auth fields
    username = Column(String(100), nullable=False)  # Not unique, set during face registration
    face_embeddings = Column(JSON, nullable=True)  # Multiple 128-dim vectors
    age_group = Column(String(20), nullable=True)  # child/teen/adult/senior
    
    # Common fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")))
    updated_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")), onupdate=lambda: datetime.now(ZoneInfo("Asia/Singapore")))
    
    # Authentication method tracking
    auth_method = Column(String(20), default="face")  # 'email', 'face', or 'both'
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the hashed password"""
        if not self.hashed_password:
            return False
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str):
        """Hash and set a new password"""
        self.hashed_password = pwd_context.hash(password)
    
    def add_face_embeddings(self, embeddings: list, age_group: str = None):
        """Add face embeddings to user profile"""
        self.face_embeddings = embeddings
        if age_group:
            self.age_group = age_group
        
        # Update auth method
        if self.email and self.hashed_password:
            self.auth_method = "both"
        else:
            self.auth_method = "face"
    
    def add_email_auth(self, email: str, password: str):
        """Add email/password authentication to face-only user"""
        self.email = email
        self.set_password(password)
        
        # Update auth method
        if self.face_embeddings:
            self.auth_method = "both"
        else:
            self.auth_method = "email"
    
    def to_dict(self):
        """Convert user to dictionary for JWT payload"""
        return {
            "user_id": self.id,
            "email": self.email,
            "username": self.username,
            "age_group": self.age_group,
            "auth_method": self.auth_method,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
