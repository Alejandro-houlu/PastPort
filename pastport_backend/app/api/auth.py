"""
Authentication API endpoints for PastPort
Handles both email/password and face recognition authentication
"""
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.user import User
from ..schemas.auth_schemas import (
    LoginRequest, RegisterRequest, FaceLoginRequest, FaceRegisterRequest,
    LinkFaceRequest, RefreshRequest, LogoutRequest, TokenResponse,
    RefreshResponse, FaceMatchResponse, MessageResponse, UserData,
    FaceMatchRequest
)
from ..utils.jwt_utils import (
    create_token_pair, verify_token, blacklist_token, refresh_access_token
)
from ..utils.face_matching import find_best_match, validate_embeddings
from ..dependencies.authentication import get_current_user, get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Email/password authentication
    
    Args:
        credentials: Email and password
        db: Database session
    
    Returns:
        JWT tokens and user data
    
    Raises:
        HTTPException: If credentials are invalid
    """
    logger.info(f"Login attempt for email: {credentials.email}")
    
    # Find user by email
    result = await db.execute(
        select(User).filter(
            User.email == credentials.email,
            User.is_active == True
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.verify_password(credentials.password):
        logger.warning(f"Failed login attempt for email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login (if you want to track this)
    user.updated_at = datetime.now(ZoneInfo("Asia/Singapore"))
    await db.commit()
    
    # Create tokens
    user_data = user.to_dict()
    tokens = create_token_pair(user_data)
    
    logger.info(f"Successful login for user: {user.id}")
    
    return TokenResponse(
        access=tokens["access"],
        refresh=tokens["refresh"],
        data=UserData(**user_data)
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Traditional email/password registration
    
    Args:
        user_data: Registration data
        db: Database session
    
    Returns:
        JWT tokens and user data
    
    Raises:
        HTTPException: If email already exists
    """
    logger.info(f"Registration attempt for email: {user_data.email}")
    
    # Check if email already exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        auth_method="email"
    )
    new_user.set_password(user_data.password)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create tokens
    user_dict = new_user.to_dict()
    tokens = create_token_pair(user_dict)
    
    logger.info(f"Successful registration for user: {new_user.id}")
    
    return TokenResponse(
        access=tokens["access"],
        refresh=tokens["refresh"],
        data=UserData(**user_dict)
    )


@router.post("/face-login", response_model=TokenResponse)
async def face_login(
    face_data: FaceLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Face recognition authentication
    
    Args:
        face_data: Face embeddings for recognition
        db: Database session
    
    Returns:
        JWT tokens and user data if face is recognized
    
    Raises:
        HTTPException: If face is not recognized or invalid
    """
    logger.info(f"Face login attempt with {len(face_data.embeddings)} embeddings")
    
    # Validate embeddings
    if not validate_embeddings(face_data.embeddings):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid face embeddings format"
        )
    
    # Get all users with face embeddings
    result = await db.execute(
        select(User).filter(
            User.face_embeddings.isnot(None),
            User.is_active == True
        )
    )
    users_with_faces = result.scalars().all()
    
    if not users_with_faces:
        logger.info("No users with face embeddings found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No face profiles found"
        )
    
    # Prepare stored embeddings for matching
    stored_embeddings = {}
    for user in users_with_faces:
        if user.face_embeddings:
            stored_embeddings[user.id] = user.face_embeddings
    
    # Find best match
    match_result = find_best_match(face_data.embeddings, stored_embeddings)
    
    if not match_result or not match_result.get("matched"):
        logger.info("No face match found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Face not recognized"
        )
    
    # Get matched user
    result = await db.execute(select(User).filter(User.id == match_result["user_id"]))
    matched_user = result.scalar_one_or_none()
    
    if not matched_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matched user not found"
        )
    
    # Update last login
    matched_user.updated_at = datetime.now(ZoneInfo("Asia/Singapore"))
    await db.commit()
    
    # Create tokens
    user_data = matched_user.to_dict()
    tokens = create_token_pair(user_data)
    
    logger.info(f"Successful face login for user: {matched_user.id} (confidence: {match_result['confidence']:.4f})")
    
    return TokenResponse(
        access=tokens["access"],
        refresh=tokens["refresh"],
        data=UserData(**user_data),
        confidence=match_result["confidence"]
    )


@router.post("/face-register", response_model=TokenResponse)
async def face_register(
    face_data: FaceRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user with face recognition
    
    Args:
        face_data: Username, face embeddings, and age group
        db: Database session
    
    Returns:
        JWT tokens and user data
    
    Raises:
        HTTPException: If face embeddings are invalid
    """
    logger.info(f"Face registration attempt for username: {face_data.username}")
    
    # Validate embeddings
    if not validate_embeddings(face_data.embeddings):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid face embeddings format"
        )
    
    # Create new user with face data
    new_user = User(
        username=face_data.username,
        auth_method="face"
    )
    new_user.add_face_embeddings(face_data.embeddings, face_data.age_group)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create tokens
    user_dict = new_user.to_dict()
    tokens = create_token_pair(user_dict)
    
    logger.info(f"Successful face registration for user: {new_user.id}")
    
    return TokenResponse(
        access=tokens["access"],
        refresh=tokens["refresh"],
        data=UserData(**user_dict)
    )


@router.post("/link-face", response_model=MessageResponse)
async def link_face(
    face_data: LinkFaceRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Link face authentication to existing email account
    
    Args:
        face_data: Face embeddings and age group
        current_user: Currently authenticated user
        db: Database session
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If embeddings are invalid or user already has face auth
    """
    logger.info(f"Link face attempt for user: {current_user.id}")
    
    # Check if user already has face authentication
    if current_user.face_embeddings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has face authentication"
        )
    
    # Validate embeddings
    if not validate_embeddings(face_data.embeddings):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid face embeddings format"
        )
    
    # Add face embeddings to user
    current_user.add_face_embeddings(face_data.embeddings, face_data.age_group)
    current_user.updated_at = datetime.now(ZoneInfo("Asia/Singapore"))
    
    await db.commit()
    
    logger.info(f"Successfully linked face to user: {current_user.id}")
    
    return MessageResponse(message="Face authentication linked successfully")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(refresh_data: RefreshRequest):
    """
    Refresh access token using refresh token
    
    Args:
        refresh_data: Refresh token
    
    Returns:
        New access token
    
    Raises:
        HTTPException: If refresh token is invalid
    """
    new_access_token = refresh_access_token(refresh_data.refresh)
    
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return RefreshResponse(access=new_access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(logout_data: LogoutRequest):
    """
    Logout user by blacklisting refresh token
    
    Args:
        logout_data: Refresh token to blacklist
    
    Returns:
        Success message
    """
    # Verify and blacklist the refresh token
    payload = verify_token(logout_data.refresh, "refresh")
    if payload:
        blacklist_token(logout_data.refresh)
    
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserData)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    
    Args:
        current_user: Currently authenticated user
    
    Returns:
        User data
    """
    return UserData(**current_user.to_dict())


@router.post("/face-match", response_model=FaceMatchResponse)
async def face_match(
    face_data: FaceMatchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Internal face matching service
    Used by frontend to test face recognition without authentication
    
    Args:
        face_data: Face embeddings to match
        db: Database session
    
    Returns:
        Match result with confidence and user ID
    """
    logger.info(f"Face match request with {len(face_data.embeddings)} embeddings")
    
    # Validate embeddings
    if not validate_embeddings(face_data.embeddings):
        return FaceMatchResponse(
            matched=False,
            confidence=0.0,
            user_id=None,
            distance=None
        )
    
    # Get all users with face embeddings
    result = await db.execute(
        select(User).filter(
            User.face_embeddings.isnot(None),
            User.is_active == True
        )
    )
    users_with_faces = result.scalars().all()
    
    if not users_with_faces:
        return FaceMatchResponse(
            matched=False,
            confidence=0.0,
            user_id=None,
            distance=None
        )
    
    # Prepare stored embeddings for matching
    stored_embeddings = {}
    for user in users_with_faces:
        if user.face_embeddings:
            stored_embeddings[user.id] = user.face_embeddings
    
    # Find best match
    match_result = find_best_match(face_data.embeddings, stored_embeddings)
    
    if not match_result:
        return FaceMatchResponse(
            matched=False,
            confidence=0.0,
            user_id=None,
            distance=None
        )
    
    return FaceMatchResponse(
        matched=match_result.get("matched", False),
        user_id=match_result.get("user_id"),
        confidence=match_result.get("confidence", 0.0),
        distance=match_result.get("distance")
    )
