"""
Pydantic schemas for Chat system
Handles validation for WebSocket messages and API responses
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# Base schemas for chat functionality
class ChatMessageRequest(BaseModel):
    """Schema for incoming chat messages via WebSocket"""
    type: str = Field(..., description="Message type (query, ping, status)")
    content: str = Field(..., max_length=5000, description="User query content")
    session_id: str = Field(..., description="Chat session identifier")
    user_id: str = Field(..., description="User identifier")
    user_age_group: Optional[str] = Field(None, description="User age group (child/teen/adult/senior)")
    message_id: Optional[str] = Field(None, description="Unique message identifier")
    image_result: Optional[Dict[str, Any]] = Field(None, description="Image recognition result context")
    timestamp: Optional[int] = Field(None, description="Client timestamp")
    
    @field_validator('user_age_group')
    def validate_age_group(cls, v):
        if v is not None and v not in ['child', 'teen', 'adult', 'senior']:
            raise ValueError('Age group must be one of: child, teen, adult, senior')
        return v


class ChatResponseBase(BaseModel):
    """Base schema for chat responses"""
    type: str = Field(..., description="Response type (thinking, response, error)")
    content: Optional[str] = Field(None, description="Response content")
    session_id: str = Field(..., description="Chat session identifier")
    message_id: Optional[str] = Field(None, description="Related message identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ChatThinkingResponse(ChatResponseBase):
    """Schema for thinking/processing status responses"""
    type: str = Field(default="thinking", description="Response type")
    stage: str = Field(..., description="Processing stage (validation, museum_query, personalization)")


class ChatFinalResponse(ChatResponseBase):
    """Schema for final chat responses"""
    type: str = Field(default="response", description="Response type")
    content: str = Field(..., description="Final response content")
    source: str = Field(..., description="Response source (museum_rag, openai_web)")
    contexts: List[Dict[str, Any]] = Field(default=[], description="RAG contexts/citations")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="Agent processing metadata")


class ChatErrorResponse(ChatResponseBase):
    """Schema for error responses"""
    type: str = Field(default="error", description="Response type")
    content: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for client handling")
    retry_possible: bool = Field(default=True, description="Whether retry is possible")


# Database-related schemas
class ChatSessionCreate(BaseModel):
    """Schema for creating new chat sessions"""
    user_id: str = Field(..., description="User identifier")
    session_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional session metadata")


class ChatSessionResponse(BaseModel):
    """Schema for chat session responses"""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Session last update timestamp")
    is_active: bool = Field(..., description="Whether session is active")
    message_count: int = Field(default=0, description="Number of messages in session")
    
    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    """Schema for creating new chat messages"""
    chat_session_id: str = Field(..., description="Chat session identifier")
    user_query: str = Field(..., max_length=5000, description="User query")
    museum_response: str = Field(..., description="Museum response")
    response_source: str = Field(..., description="Response source")
    user_age_group: Optional[str] = Field(None, description="User age group")
    contexts: Optional[List[Dict[str, Any]]] = Field(None, description="RAG contexts")
    image_result: Optional[Dict[str, Any]] = Field(None, description="Image recognition result")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")
    
    @field_validator('response_source')
    def validate_response_source(cls, v):
        if v not in ['museum_rag', 'openai_web']:
            raise ValueError('Response source must be either museum_rag or openai_web')
        return v


class ChatMessageResponse(BaseModel):
    """Schema for chat message responses"""
    message_id: str = Field(..., description="Message identifier")
    session_id: str = Field(..., description="Session identifier")
    user_query: str = Field(..., description="User query")
    museum_response: str = Field(..., description="Museum response")
    response_source: str = Field(..., description="Response source")
    user_age_group: Optional[str] = Field(None, description="User age group")
    contexts: Optional[List[Dict[str, Any]]] = Field(None, description="RAG contexts")
    image_result: Optional[Dict[str, Any]] = Field(None, description="Image recognition result")
    timestamp: datetime = Field(..., description="Message timestamp")
    formatted_contexts: List[Dict[str, Any]] = Field(default=[], description="User-friendly contexts")
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Schema for chat history responses"""
    session: ChatSessionResponse = Field(..., description="Session information")
    messages: List[ChatMessageResponse] = Field(default=[], description="Session messages")
    total_messages: int = Field(default=0, description="Total message count")


# Agent-specific schemas
class AgentContext(BaseModel):
    """Schema for agent processing context"""
    original_query: str = Field(..., description="Original user query")
    session_id: str = Field(..., description="Chat session ID")
    user_id: str = Field(..., description="User ID")
    user_age_group: Optional[str] = Field(None, description="User age group")
    message_id: str = Field(..., description="Message ID")
    image_result: Optional[Dict[str, Any]] = Field(None, description="Image recognition context")
    chat_history: List[Dict[str, Any]] = Field(default=[], description="Recent chat history")
    processing_stage: str = Field(default="initial", description="Current processing stage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")


class AgentResponse(BaseModel):
    """Schema for agent processing responses"""
    success: bool = Field(..., description="Whether processing was successful")
    content: str = Field(..., description="Response content")
    source: str = Field(..., description="Response source")
    contexts: List[Dict[str, Any]] = Field(default=[], description="RAG contexts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    error: Optional[str] = Field(None, description="Error message if failed")


# OpenAI integration schemas
class OpenAIFallbackRequest(BaseModel):
    """Schema for OpenAI fallback requests"""
    query: str = Field(..., description="User query for fallback")
    context: Optional[str] = Field(None, description="Additional context")
    max_tokens: int = Field(default=500, description="Maximum response tokens")


class OpenAIPersonalizationRequest(BaseModel):
    """Schema for OpenAI personalization requests"""
    response: str = Field(..., description="Response to personalize")
    age_group: str = Field(..., description="Target age group")
    chat_history: List[Dict[str, Any]] = Field(default=[], description="Chat history context")
    max_tokens: int = Field(default=500, description="Maximum response tokens")
    
    @field_validator('age_group')
    def validate_age_group(cls, v):
        if v not in ['child', 'teen', 'adult', 'senior']:
            raise ValueError('Age group must be one of: child, teen, adult, senior')
        return v
