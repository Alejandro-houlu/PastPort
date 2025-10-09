"""
Chat models for PastPort Museum RAG chat system
Supports session-based chat history with user context
"""
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class ChatSession(Base):
    """Chat session model for tracking conversation contexts"""
    __tablename__ = "chat_sessions"
    
    # Primary key - UUID for unique session identification
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to users table
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Session metadata
    created_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")))
    updated_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")), onupdate=lambda: datetime.now(ZoneInfo("Asia/Singapore")))
    is_active = Column(Boolean, default=True)
    
    # Optional session context
    session_metadata = Column(JSON, nullable=True)  # Store additional session context
    
    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert chat session to dictionary"""
        return {
            "session_id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
            "message_count": len(self.messages) if self.messages else 0
        }


class ChatMessage(Base):
    """Chat message model for storing query/response pairs"""
    __tablename__ = "chat_messages"
    
    # Primary key - UUID for unique message identification
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to chat_sessions table
    chat_session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # Message content
    user_query = Column(Text, nullable=False)
    museum_response = Column(Text, nullable=False)
    
    # Response metadata
    response_source = Column(String(50), nullable=False)  # "museum_rag_personalized", etc.
    user_age_group = Column(String(20), nullable=True)  # child/teen/adult/senior
    
    # RAG context and citations
    contexts = Column(JSON, nullable=True)  # Store RAG contexts/citations
    
    # Image recognition context (optional)
    image_result = Column(JSON, nullable=True)  # Store image recognition results
    
    # Timestamps
    timestamp = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")))
    
    # Agent processing metadata
    processing_metadata = Column(JSON, nullable=True)  # Store agent processing info
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def to_dict(self):
        """Convert chat message to dictionary"""
        return {
            "message_id": self.id,
            "session_id": self.chat_session_id,
            "user_query": self.user_query,
            "museum_response": self.museum_response,
            "response_source": self.response_source,
            "user_age_group": self.user_age_group,
            "contexts": self.contexts,
            "image_result": self.image_result,
            "timestamp": self.timestamp,
            "processing_metadata": self.processing_metadata
        }
    
    def get_formatted_contexts(self):
        """Get user-friendly formatted contexts/citations"""
        if not self.contexts:
            return []
        
        formatted = []
        for context in self.contexts:
            formatted_context = {
                "title": context.get("source", "Unknown Source"),
                "species": context.get("metadata", {}).get("species", "unknown"),
                "relevance": round(context.get("relevance_score", 0.0), 2),
                "page": context.get("metadata", {}).get("page", "N/A")
            }
            formatted.append(formatted_context)
        
        return formatted
