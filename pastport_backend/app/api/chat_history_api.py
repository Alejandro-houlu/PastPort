"""
API endpoints for Chat History
Provides access to user's chat session history
"""
import logging
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.models.artifact import Artifact
from app.models.user import User
from app.dependencies.authentication import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat-history", tags=["chat_history"])


# Pydantic schemas
class ChatHistoryResponse(BaseModel):
    """Response model for chat history item"""
    session_id: str
    artifact_id: str | None
    artifact_name: str | None
    last_message: str
    timestamp: datetime
    message_count: int
    
    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    user_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's chat session history with last message preview
    Returns up to {limit} sessions, ordered by most recent activity
    
    Args:
        user_id: User ID to get chat history for
        limit: Maximum number of sessions to return (default 10)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of chat sessions with preview information
    """
    try:
        # Verify user_id matches current user
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other users' chat history"
            )
        
        # Query for user's chat sessions with messages
        result = await db.execute(
            select(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .options(selectinload(ChatSession.messages))
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
        )
        sessions = result.scalars().all()
        
        # Format response
        response_list = []
        for session in sessions:
            # Get the last message
            last_message_text = "No messages yet"
            artifact_id = None
            artifact_name = None
            
            if session.messages:
                # Sort messages by timestamp to get the last one
                sorted_messages = sorted(session.messages, key=lambda m: m.timestamp, reverse=True)
                last_message = sorted_messages[0]
                
                # Use user query as preview
                last_message_text = last_message.user_query[:100]
                if len(last_message.user_query) > 100:
                    last_message_text += "..."
                
                # Try to extract artifact info from image_result
                if last_message.image_result and isinstance(last_message.image_result, dict):
                    entity_id = last_message.image_result.get('entity_id')
                    if entity_id:
                        # Try to get artifact info
                        artifact_result = await db.execute(
                            select(Artifact).filter(Artifact.id == entity_id)
                        )
                        artifact = artifact_result.scalar_one_or_none()
                        if artifact:
                            artifact_id = artifact.id
                            artifact_name = artifact.artifact_name
                        else:
                            # Fallback to label from image_result
                            artifact_name = last_message.image_result.get('label', 'Unknown Artifact')
            
            response_list.append({
                "session_id": session.id,
                "artifact_id": artifact_id,
                "artifact_name": artifact_name,
                "last_message": last_message_text,
                "timestamp": session.updated_at,
                "message_count": len(session.messages)
            })
        
        logger.info(f"Retrieved {len(response_list)} chat sessions for user {user_id}")
        
        return response_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=dict)
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all messages for a specific chat session
    
    Args:
        session_id: Chat session ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Session details with all messages
    """
    try:
        # Query for session
        result = await db.execute(
            select(ChatSession)
            .filter(ChatSession.id == session_id)
            .options(selectinload(ChatSession.messages))
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Verify user owns this session
        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other users' chat sessions"
            )
        
        # Format messages
        messages = []
        for msg in sorted(session.messages, key=lambda m: m.timestamp):
            messages.append({
                "message_id": msg.id,
                "user_query": msg.user_query,
                "museum_response": msg.museum_response,
                "timestamp": msg.timestamp,
                "source": msg.response_source,
                "contexts": msg.contexts
            })
        
        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": len(messages),
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session messages: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session messages: {str(e)}"
        )
