"""
State definitions for PastPort Museum Chat LangGraph system
Defines the shared state object passed between agents
"""
from typing import Dict, Any, List, Optional, Callable
from typing_extensions import TypedDict


class ChatState(TypedDict):
    """State object passed between agents in the LangGraph flow"""
    # Input context
    original_query: str
    session_id: str
    user_id: str
    user_age_group: Optional[str]
    message_id: str
    image_result: Optional[Dict[str, Any]]
    
    # Processing context
    chat_history: List[Dict[str, Any]]
    processing_stage: str
    websocket_callback: Optional[Callable]  # For sending thinking updates
    
    # Agent results
    manager_validation: Optional[Dict[str, Any]]
    museum_response: Optional[Dict[str, Any]]
    comms_response: Optional[Dict[str, Any]]
    
    # Final output
    final_response: str
    response_source: str
    contexts: List[Dict[str, Any]]
    processing_metadata: Dict[str, Any]
    
    # Error handling
    error: Optional[str]
    success: bool
