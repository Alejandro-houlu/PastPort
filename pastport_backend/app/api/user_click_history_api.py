"""
API endpoints for User Click History
Tracks which artifacts users have clicked on to populate the chat interface
"""
import logging
from typing import List
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user_click_history import UserClickHistory
from app.models.artifact import Artifact
from app.models.user import User
from app.dependencies.authentication import get_current_user
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user-clicks", tags=["user_click_history"])


# Pydantic schemas
class ClickRecordRequest(BaseModel):
    """Request model for recording an artifact click"""
    artifact_name: str
    source: str = "camera"  # Default source


class ClickRecordResponse(BaseModel):
    """Response model for click recording"""
    success: bool
    message: str
    click_id: str


class ArtifactClickResponse(BaseModel):
    """Response model for artifact with click info"""
    id: str
    artifact_name: str
    description: str | None
    museum_location: str | None
    artifact_location: str | None
    image_url: str | None
    isDisplay: bool
    clicked_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/record", response_model=ClickRecordResponse, status_code=status.HTTP_201_CREATED)
async def record_artifact_click(
    request: ClickRecordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record a user's click on an artifact
    Updates timestamp if the user has already clicked this artifact
    User is automatically determined from JWT token
    
    Args:
        request: Click record request with artifact_id and source
        db: Database session
        current_user: Current authenticated user (from JWT token)
        
    Returns:
        ClickRecordResponse with success status and click_id
    """
    try:
        # Use current_user.id from JWT token
        user_id = current_user.id
        
        # Verify artifact exists
        result = await db.execute(
            select(Artifact).filter(Artifact.artifact_name == request.artifact_name)
        )
        artifact = result.scalar_one_or_none()
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact with name {request.artifact_name} not found"
            )
        
        # Check if user already has a click record for this artifact
        result = await db.execute(
            select(UserClickHistory).filter(
                UserClickHistory.user_id == user_id,
                UserClickHistory.artifact_id == artifact.id
            )
        )
        existing_click = result.scalar_one_or_none()
        
        if existing_click:
            # Update the timestamp to move it to the top of recent clicks
            existing_click.clicked_at = datetime.now(ZoneInfo("Asia/Singapore"))
            existing_click.source = request.source
            await db.commit()
            await db.refresh(existing_click)
            
            logger.info(f"Updated click timestamp for user {user_id} on artifact {request.artifact_name}")
            
            return ClickRecordResponse(
                success=True,
                message="Click timestamp updated",
                click_id=existing_click.id
            )
        else:
            # Create new click record
            new_click = UserClickHistory(
                user_id=user_id,
                artifact_id=artifact.id,
                source=request.source
            )
            db.add(new_click)
            await db.commit()
            await db.refresh(new_click)
            
            logger.info(f"Recorded new click for user {user_id} on artifact {request.artifact_name}")
            
            return ClickRecordResponse(
                success=True,
                message="Click recorded successfully",
                click_id=new_click.id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording click: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record click: {str(e)}"
        )


@router.get("/{user_id}/recent", response_model=List[ArtifactClickResponse])
async def get_recent_clicks(
    user_id: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the most recent distinct artifacts that a user has clicked on
    Returns up to {limit} artifacts, ordered by most recent click
    
    Args:
        user_id: User ID to get clicks for
        limit: Maximum number of artifacts to return (default 5)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of artifacts with click timestamps
    """
    try:
        # Verify user_id matches current user
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other users' click history"
            )
        
        # Query for recent clicks - get all clicks for this user, ordered by most recent
        result = await db.execute(
            select(UserClickHistory, Artifact)
            .join(Artifact, UserClickHistory.artifact_id == Artifact.id)
            .filter(UserClickHistory.user_id == user_id)
            .order_by(desc(UserClickHistory.clicked_at))
        )
        all_clicks = result.all()
        
        # Filter to get distinct artifacts (keeping only the most recent click per artifact)
        seen_artifacts = set()
        distinct_clicks = []
        for click, artifact in all_clicks:
            if artifact.id not in seen_artifacts:
                seen_artifacts.add(artifact.id)
                distinct_clicks.append((click, artifact))
                if len(distinct_clicks) >= limit:
                    break
        
        # Format response with S3 presigned URLs
        response_list = []
        for click, artifact in distinct_clicks:
            # Get first image from S3
            image_url = None
            try:
                # Construct S3 folder path: pastport/artifact_images/{artifact_name}_{id}/
                folder_path = f"pastport/artifact_images/{artifact.artifact_name}_{artifact.id}/"
                logger.info(f"Fetching first image from S3 folder: {folder_path}")
                
                # Get first image key from folder
                first_image_key = s3_service.get_first_image(folder_path)
                if first_image_key:
                    # Generate presigned URL (valid for 1 hour)
                    image_url = s3_service.generate_presigned_url(first_image_key, expiration=3600)
                    if image_url:
                        logger.info(f"Generated presigned URL for artifact {artifact.artifact_name}")
            except Exception as e:
                logger.error(f"Error getting S3 image for artifact {artifact.artifact_name}: {e}")
            
            # Fallback to artifact.image_url if S3 fails
            if not image_url:
                image_url = artifact.image_url
            
            response_list.append({
                "id": artifact.id,
                "artifact_name": artifact.artifact_name,
                "description": artifact.description,
                "museum_location": artifact.museum_location,
                "artifact_location": artifact.artifact_location,
                "image_url": image_url,
                "isDisplay": artifact.isDisplay,
                "clicked_at": click.clicked_at
            })
        
        logger.info(f"Retrieved {len(response_list)} recent clicks for user {user_id}")
        
        return response_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recent clicks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recent clicks: {str(e)}"
        )
