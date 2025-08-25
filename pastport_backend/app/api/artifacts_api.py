"""
Artifacts API for PastPort
Handles artifact image retrieval from S3 with database integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import io
import logging

from ..database import get_db
from ..models.artifact import Artifact
from ..models.user import User
from ..dependencies.authentication import get_current_user
from ..services.s3_service import s3_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/artifacts/{artifact_name}/image")
async def get_artifact_image(
    artifact_name: str,
    response_type: str = Query(default="presigned_url", description="Response type: 'presigned_url' or 'stream'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the first image for a specific artifact from S3
    
    Args:
        artifact_name: Name of the artifact (e.g., 'rafflesia')
        response_type: 'presigned_url' (default) or 'stream'
        current_user: Authenticated user (JWT required)
        db: Database session
    
    Returns:
        - presigned_url: JSON with temporary URL for secure access
        - stream: Direct image stream response
    
    Raises:
        HTTPException: If artifact not found, no images available, or S3 error
    """
    try:
        # Query artifact from database by name
        result = await db.execute(
            select(Artifact).filter(Artifact.artifact_name == artifact_name)
        )
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            logger.warning(f"Artifact not found: {artifact_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact '{artifact_name}' not found"
            )
        
        # Construct S3 folder path: pastport/artifact_images/{artifact_name}_{id}/
        folder_path = f"pastport/artifact_images/{artifact_name}_{artifact.id}/"
        logger.info(f"Looking for images in S3 folder: {folder_path}")
        
        # Get first image from S3 folder
        first_image_key = s3_service.get_first_image(folder_path)
        
        if not first_image_key:
            logger.warning(f"No images found in folder: {folder_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No images found for artifact '{artifact_name}'"
            )
        
        # Handle different response types
        if response_type == "stream":
            return await _stream_image_response(first_image_key)
        else:  # Default to presigned_url
            return await _presigned_url_response(first_image_key, artifact_name)
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting artifact image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving artifact image"
        )


async def _stream_image_response(image_key: str) -> StreamingResponse:
    """
    Stream image directly from S3
    
    Args:
        image_key: S3 object key for the image
    
    Returns:
        StreamingResponse with image content
    """
    try:
        # Download image content
        image_content = s3_service.download_object(image_key)
        
        if not image_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download image from S3"
            )
        
        # Get image metadata for proper content type
        object_info = s3_service.get_object_info(image_key)
        content_type = object_info.get('content_type', 'image/jpeg') if object_info else 'image/jpeg'
        
        # Create streaming response
        return StreamingResponse(
            io.BytesIO(image_content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={image_key.split('/')[-1]}",
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )
        
    except Exception as e:
        logger.error(f"Error streaming image {image_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stream image"
        )


async def _presigned_url_response(image_key: str, artifact_name: str) -> JSONResponse:
    """
    Generate presigned URL for secure image access
    
    Args:
        image_key: S3 object key for the image
        artifact_name: Name of the artifact
    
    Returns:
        JSONResponse with presigned URL and metadata
    """
    try:
        # Generate presigned URL (valid for 1 hour)
        presigned_url = s3_service.generate_presigned_url(image_key, expiration=3600)
        
        if not presigned_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate secure image URL"
            )
        
        # Get image metadata
        object_info = s3_service.get_object_info(image_key)
        
        response_data = {
            "artifact_name": artifact_name,
            "image_url": presigned_url,
            "expires_in": 3600,  # 1 hour in seconds
            "image_key": image_key,
            "metadata": {
                "content_type": object_info.get('content_type') if object_info else None,
                "content_length": object_info.get('content_length') if object_info else None,
                "last_modified": object_info.get('last_modified').isoformat() if object_info and object_info.get('last_modified') else None
            }
        }
        
        return JSONResponse(
            content=response_data,
            headers={
                "Cache-Control": "private, max-age=300"  # Cache for 5 minutes
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating presigned URL for {image_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate secure image URL"
        )


@router.get("/artifacts/{artifact_name}/images")
async def list_artifact_images(
    artifact_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all images available for a specific artifact
    
    Args:
        artifact_name: Name of the artifact (e.g., 'rafflesia')
        current_user: Authenticated user (JWT required)
        db: Database session
    
    Returns:
        JSON with list of available images and their metadata
    
    Raises:
        HTTPException: If artifact not found or S3 error
    """
    try:
        # Query artifact from database by name
        result = await db.execute(
            select(Artifact).filter(Artifact.artifact_name == artifact_name)
        )
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            logger.warning(f"Artifact not found: {artifact_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact '{artifact_name}' not found"
            )
        
        # Construct S3 folder path
        folder_path = f"pastport/artifact_images/{artifact_name}_{artifact.id}/"
        logger.info(f"Listing images in S3 folder: {folder_path}")
        
        # Get all objects in folder
        object_keys = s3_service.list_folder_contents(folder_path)
        
        # Filter for image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        image_files = [
            key for key in object_keys 
            if any(key.lower().endswith(ext) for ext in image_extensions)
        ]
        
        if not image_files:
            return JSONResponse(
                content={
                    "artifact_name": artifact_name,
                    "artifact_id": artifact.id,
                    "folder_path": folder_path,
                    "images": [],
                    "total_images": 0
                }
            )
        
        # Sort images for consistent ordering
        image_files.sort()
        
        # Prepare response with image metadata
        images_data = []
        for image_key in image_files:
            object_info = s3_service.get_object_info(image_key)
            images_data.append({
                "image_key": image_key,
                "filename": image_key.split('/')[-1],
                "content_type": object_info.get('content_type') if object_info else None,
                "content_length": object_info.get('content_length') if object_info else None,
                "last_modified": object_info.get('last_modified').isoformat() if object_info and object_info.get('last_modified') else None
            })
        
        return JSONResponse(
            content={
                "artifact_name": artifact_name,
                "artifact_id": artifact.id,
                "folder_path": folder_path,
                "images": images_data,
                "total_images": len(images_data)
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing artifact images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while listing artifact images"
        )
