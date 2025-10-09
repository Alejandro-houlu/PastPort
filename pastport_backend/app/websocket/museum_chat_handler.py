"""
WebSocket handler for PastPort Museum Chat with three-agent LangGraph system
Handles real-time chat communication with Manager -> Museum -> Comms agent flow
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional, Callable
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from app.dependencies.rag import get_rag_status
from app.agents.build_graph import process_museum_chat
from app.schemas.chat_schemas import ChatMessageRequest

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Enhanced chat message model for WebSocket communication"""
    type: str  # "query", "ping", "status"
    content: str  # Changed from 'message' to 'content' for consistency
    session_id: str
    user_id: str
    user_age_group: Optional[str] = "adult"
    message_id: Optional[str] = None
    image_result: Optional[Dict[str, Any]] = None
    timestamp: Optional[int] = None


class ChatResponse(BaseModel):
    """Enhanced chat response model for WebSocket communication"""
    type: str  # "thinking", "response", "error", "status", "pong"
    content: Optional[str] = None
    session_id: str
    message_id: Optional[str] = None
    stage: Optional[str] = None  # For thinking updates
    source: Optional[str] = None  # Response source (museum_rag, openai_web, etc.)
    contexts: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None


class ConnectionManager:
    """Manages WebSocket connections for museum chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Museum chat client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Museum chat client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: dict):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)


# Global connection manager instance
manager = ConnectionManager()


async def handle_museum_chat_websocket_connection(websocket: WebSocket, client_id: str = None):
    """
    Handle WebSocket connection for museum chat
    
    Args:
        websocket: FastAPI WebSocket instance
        client_id: Optional client identifier
    """
    if client_id is None:
        client_id = f"client_{id(websocket)}"
    
    await manager.connect(websocket, client_id)
    
    # Send initial status
    try:
        rag_status = get_rag_status()
        initial_response = ChatResponse(
            type="status",
            message="Connected to Museum Chat",
            metadata={
                "rag_status": rag_status["status"],
                "client_id": client_id,
                "available_commands": ["query", "ping", "status"]
            }
        )
        await manager.send_message(client_id, initial_response.model_dump())
    except Exception as e:
        logger.error(f"Error sending initial status to {client_id}: {e}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                chat_message = ChatMessage(**message_data)
                
                logger.info(f"Received message from {client_id}: {chat_message.type}")
                logger.info(f"Received message from {client_id}: {chat_message}")
                
                # Handle different message types
                if chat_message.type == "query":
                    await handle_query_message(client_id, chat_message)
                elif chat_message.type == "ping":
                    await handle_ping_message(client_id, chat_message)
                elif chat_message.type == "status":
                    await handle_status_message(client_id, chat_message)
                else:
                    # Unknown message type
                    error_response = ChatResponse(
                        type="error",
                        message=f"Unknown message type: {chat_message.type}",
                        session_id=chat_message.session_id
                    )
                    await manager.send_message(client_id, error_response.dict())
                    
            except ValidationError as e:
                # Invalid message format
                error_response = ChatResponse(
                    type="error",
                    message=f"Invalid message format: {str(e)}"
                )
                await manager.send_message(client_id, error_response.dict())
                
            except json.JSONDecodeError:
                # Invalid JSON
                error_response = ChatResponse(
                    type="error",
                    message="Invalid JSON format"
                )
                await manager.send_message(client_id, error_response.dict())
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Museum chat client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in museum chat WebSocket for {client_id}: {e}")
        manager.disconnect(client_id)


async def handle_query_message(client_id: str, message: ChatMessage):
    """Handle a query message from the client using the three-agent LangGraph system"""
    try:
        # Generate message ID if not provided
        message_id = message.message_id or str(uuid.uuid4())
        
        # Log user information for verification
        user_name = getattr(message, 'user_name', 'Unknown')
        logger.info(f"Processing query from {client_id}: '{message.content[:50]}...'")
        logger.info(f"👤 User: {user_name} (ID: {message.user_id}, Age: {message.user_age_group})")
        
        # Create WebSocket callback for sending thinking updates
        async def websocket_callback(update: Dict[str, Any]):
            """Send thinking updates to the WebSocket client"""
            try:
                thinking_response = ChatResponse(
                    type=update.get("type", "thinking"),
                    content=update.get("content"),
                    session_id=message.session_id,
                    message_id=message_id,
                    stage=update.get("stage"),
                    metadata={"client_id": client_id}
                )
                await manager.send_message(client_id, thinking_response.dict())
            except Exception as e:
                logger.error(f"Error sending thinking update to {client_id}: {e}")
        
        # Process query through the three-agent LangGraph system
        agent_result = await process_museum_chat(
            original_query=message.content,
            session_id=message.session_id,
            user_id=message.user_id,
            message_id=message_id,
            user_age_group=message.user_age_group or "adult",
            image_result=message.image_result,
            websocket_callback=websocket_callback
        )
        
        if agent_result["success"]:
            # Send successful final response
            response = ChatResponse(
                type="response",
                content=agent_result["response"],
                session_id=message.session_id,
                message_id=message_id,
                source=agent_result["source"],
                contexts=agent_result["contexts"],
                metadata=agent_result["metadata"]
            )
            
            await manager.send_message(client_id, response.dict())
            logger.info(
                f"Three-agent response sent to {client_id} "
                f"(source: {agent_result['source']}, length: {len(agent_result['response'])})"
            )
            
            # Send recommendations if available
            if agent_result.get("recommended_questions"):
                logger.info(f"Sending question recommendations to {client_id}")
                recommendation_response = ChatResponse(
                    type="recommendations",
                    session_id=message.session_id,
                    message_id=message_id,
                    metadata={
                        "recommendations": agent_result["recommended_questions"]
                    }
                )
                await manager.send_message(client_id, recommendation_response.dict())
                logger.info(f"Question recommendations sent to {client_id}")
            
            # Send artifact header update if available
            if agent_result.get("artifact_data"):
                logger.info(f"Sending artifact header update to {client_id}")
                header_update_response = ChatResponse(
                    type="header_update",
                    session_id=message.session_id,
                    message_id=message_id,
                    metadata={
                        "artifact_data": agent_result["artifact_data"]
                    }
                )
                await manager.send_message(client_id, header_update_response.dict())
                logger.info(f"Artifact header update sent to {client_id}")
        else:
            # Send error response
            error_response = ChatResponse(
                type="error",
                content=agent_result.get("error"),  # User-friendly error message
                session_id=message.session_id,
                message_id=message_id,
                metadata={
                    **agent_result["metadata"],
                    "error": agent_result.get("error"),
                    "client_id": client_id
                }
            )
            await manager.send_message(client_id, error_response.dict())
            logger.warning(f"Three-agent processing error for {client_id}: {agent_result.get('error')}")
        
    except Exception as e:
        logger.error(f"Error processing query for {client_id}: {e}", exc_info=True)
        error_response = ChatResponse(
            type="error",
            content="I apologize, but I encountered an unexpected error while processing your query. Please try again.",
            session_id=message.session_id,
            message_id=message.message_id or str(uuid.uuid4()),
            metadata={"error": str(e), "client_id": client_id, "system_error": True}
        )
        await manager.send_message(client_id, error_response.dict())


async def handle_ping_message(client_id: str, message: ChatMessage):
    """Handle a ping message from the client"""
    pong_response = ChatResponse(
        type="pong",
        message="pong",
        session_id=message.session_id,
        metadata={"timestamp": "now"}
    )
    await manager.send_message(client_id, pong_response.dict())


async def handle_status_message(client_id: str, message: ChatMessage):
    """Handle a status request from the client"""
    try:
        rag_status = get_rag_status()
        status_response = ChatResponse(
            type="status",
            message="System status retrieved",
            session_id=message.session_id,
            metadata={
                "rag_status": rag_status,
                "connected_clients": len(manager.active_connections)
            }
        )
        await manager.send_message(client_id, status_response.dict())
    except Exception as e:
        error_response = ChatResponse(
            type="error",
            message=f"Error retrieving status: {str(e)}",
            session_id=message.session_id
        )
        await manager.send_message(client_id, error_response.dict())
