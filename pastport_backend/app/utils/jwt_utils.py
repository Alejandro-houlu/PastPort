"""
JWT utilities for PastPort authentication
Handles token creation, validation, and management
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pastport-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Token blacklist (in production, use Redis or database)
blacklisted_tokens = set()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new access token
    
    Args:
        data: Payload data to encode in token
        expires_delta: Custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    now = datetime.now(ZoneInfo("Asia/Singapore"))
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access"
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a new refresh token
    
    Args:
        data: Payload data to encode in token
    
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    now = datetime.now(ZoneInfo("Asia/Singapore"))
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "refresh"
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')
    
    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            return None
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.now(ZoneInfo("Asia/Singapore")).timestamp() > exp:
            return None
        
        return payload
    
    except JWTError:
        return None


def blacklist_token(token: str):
    """
    Add token to blacklist
    
    Args:
        token: JWT token to blacklist
    """
    blacklisted_tokens.add(token)


def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted
    
    Args:
        token: JWT token to check
    
    Returns:
        True if blacklisted, False otherwise
    """
    return token in blacklisted_tokens


def create_token_pair(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user
    
    Args:
        user_data: User data to encode in tokens
    
    Returns:
        Dictionary with 'access' and 'refresh' tokens
    """
    # Create minimal payload for tokens
    token_payload = {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "auth_method": user_data["auth_method"]
    }
    
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token({"user_id": user_data["user_id"]})
    
    return {
        "access": access_token,
        "refresh": refresh_token
    }


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Create new access token from valid refresh token
    
    Args:
        refresh_token: Valid refresh token
    
    Returns:
        New access token if refresh token is valid, None otherwise
    """
    payload = verify_token(refresh_token, "refresh")
    if not payload:
        return None
    
    # Create new access token with minimal payload
    new_payload = {"user_id": payload["user_id"]}
    return create_access_token(new_payload)
