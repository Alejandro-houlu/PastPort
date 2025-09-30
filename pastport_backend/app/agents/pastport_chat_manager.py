"""
PastPort Chat Manager Agent
Handles query validation, safety checks, and chat history retrieval
"""
import logging
from typing import Dict, Any, List

from app.services.openai_service import openai_service
from app.models.chat import ChatMessage, ChatSession
from app.database import get_db
from .state import ChatState

logger = logging.getLogger(__name__)


class PastPortChatManager:
    """
    Manager Agent for PastPort Museum Chat System
    
    Responsibilities:
    - Query validation and safety checks
    - Chat history retrieval from database
    - Initial processing coordination
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PastPortChatManager")
    
    def get_validation_prompt(self, query: str) -> List[Dict[str, str]]:
        """
        Generate prompt for query validation
        
        Args:
            query: User's original query to validate
            
        Returns:
            List of message objects for OpenAI chat completion
        """
        system_prompt = """You are a museum chat manager responsible for validating user queries.

Your tasks:
1. Check if the query is appropriate for a museum setting
2. Identify if it's potentially offensive, harmful, or inappropriate 
3. Determine if it's a valid question that can be processed

VALIDATION CRITERIA:
✅ ACCEPT: 
- Questions about natural history, science, exhibits, educational content
- General curiosity about nature, animals, plants, geology, fossils
- Questions about museum operations, visiting information
- Educational queries about specimens or artifacts
- Even off-topic questions (these will be handled by fallback systems)

❌ REJECT:
- Offensive language, inappropriate content, spam
- Requests for harmful information
- Abusive or threatening language
- Content inappropriate for a family museum environment

Response format:
- If VALID: respond with "VALID"
- If INVALID: respond with "INVALID: [brief reason]"

Keep your response very brief and direct."""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Validate this museum visitor query: '{query}'"}
        ]
    
    async def retrieve_chat_history(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve chat history from database for context
        
        Args:
            session_id: Chat session identifier
            user_id: User identifier
            
        Returns:
            List of previous chat messages for context
        """
        try:
            self.logger.info(f"Retrieving chat history for session {session_id}")
            
            async for db in get_db():
                from sqlalchemy import select
                
                # First check if session exists
                session_stmt = select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id
                )
                session_result = await db.execute(session_stmt)
                session_exists = session_result.scalar_one_or_none()
                
                if not session_exists:
                    self.logger.info(f"No existing session found for {session_id}")
                    return []
                
                # Retrieve recent messages from this session
                messages_stmt = select(ChatMessage).where(
                    ChatMessage.chat_session_id == session_id
                ).order_by(ChatMessage.timestamp.desc()).limit(10)
                messages_result = await db.execute(messages_stmt)
                messages = messages_result.scalars().all()
                
                # Convert to dict format and reverse to chronological order
                chat_history = [msg.to_dict() for msg in reversed(messages)]
                
                self.logger.info(f"Retrieved {len(chat_history)} messages from chat history")
                return chat_history
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve chat history: {str(e)}")
            return []  # Return empty history on error to not fail the entire process
    
    async def process_entry(self, state: ChatState) -> ChatState:
        """
        Entry processing method for the Manager Agent
        Handles query validation and chat history retrieval
        
        Args:
            state: Current chat state object
            
        Returns:
            Updated chat state after manager entry processing
        """
        self.logger.info(f"PastPort Chat Manager ENTRY processing query: '{state['original_query'][:50]}...'")
        
        try:
            # Send thinking update to WebSocket
            if state.get('websocket_callback'):
                await state['websocket_callback']({
                    "type": "thinking",
                    "content": "Validating your question and checking chat history...",
                    "stage": "validation",
                    "session_id": state['session_id'],
                    "message_id": state['message_id']
                })
            
            # Step 1: Validate the user query
            self.logger.info("Starting query validation")
            validation_messages = self.get_validation_prompt(state['original_query'])
            
            validation_result = await openai_service.chat_completion(
                messages=validation_messages,
                model="gpt-3.5-turbo",  # Use cheaper model for validation
                max_tokens=50,
                temperature=0.3  # Low temperature for consistent validation
            )
            
            if not validation_result['success']:
                error_msg = f"Query validation failed: {validation_result.get('error')}"
                self.logger.error(error_msg)
                state['error'] = error_msg
                state['success'] = False
                return state
            
            # Parse validation response
            validation_response = validation_result['content'].strip().upper()
            is_valid = validation_response.startswith("VALID")
            
            self.logger.info(f"Validation result: {validation_response}")
            
            if not is_valid:
                error_msg = f"Query rejected during validation: {validation_response}"
                self.logger.warning(error_msg)
                state['error'] = error_msg
                state['success'] = False
                return state
            
            # Step 2: Retrieve chat history for context
            self.logger.info("Retrieving chat history")
            chat_history = await self.retrieve_chat_history(
                state['session_id'], 
                state['user_id']
            )
            
            # Step 3: Store manager validation results
            state['manager_validation'] = {
                "is_valid": is_valid,
                "validation_response": validation_response,
                "chat_history_count": len(chat_history),
                "processing_timestamp": "now"  # TODO: Use proper timestamp
            }
            
            state['chat_history'] = chat_history
            state['processing_stage'] = "validated"
            
            self.logger.info(
                f"Manager ENTRY processing completed successfully. "
                f"Query valid: {is_valid}, History items: {len(chat_history)}"
            )
            
            return state
            
        except Exception as e:
            error_msg = f"PastPort Chat Manager ENTRY processing failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            state['error'] = error_msg
            state['success'] = False
            return state

    async def process_exit(self, state: ChatState) -> ChatState:
        """
        Exit processing method for the Manager Agent
        Handles final response coordination and formatting
        
        Args:
            state: Current chat state object (after Comms Agent processing)
            
        Returns:
            Updated chat state with final response ready for delivery
        """
        self.logger.info(f"PastPort Chat Manager EXIT processing for session: {state['session_id']}")
        
        try:
            # Send thinking update to WebSocket
            if state.get('websocket_callback'):
                await state['websocket_callback']({
                    "type": "thinking",
                    "content": "Finalizing response and preparing delivery...",
                    "stage": "manager_exit",
                    "session_id": state['session_id'],
                    "message_id": state['message_id']
                })
            
            # Ensure we have all required data from previous agents
            if not state.get('comms_response'):
                error_msg = "Manager EXIT: No communications response available"
                self.logger.error(error_msg)
                state['error'] = error_msg
                state['success'] = False
                return state
            
            # The final response is already set by Comms Agent, but Manager can do final formatting
            # This is where Manager could add additional formatting, logging, or coordination
            
            # Add Manager exit metadata
            if 'processing_metadata' not in state:
                state['processing_metadata'] = {}
            
            state['processing_metadata']['manager_exit'] = {
                "final_coordination": True,
                "response_length": len(state['final_response']),
                "response_source": state['response_source'],
                "context_count": len(state.get('contexts', [])),
                "processing_complete": True
            }
            
            # Mark processing stage as completed
            state['processing_stage'] = "manager_coordinated"
            
            self.logger.info(
                f"Manager EXIT processing completed successfully. "
                f"Final response length: {len(state['final_response'])}, "
                f"Source: {state['response_source']}"
            )
            
            return state
            
        except Exception as e:
            error_msg = f"PastPort Chat Manager EXIT processing failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            state['error'] = error_msg
            state['success'] = False
            return state

    # Keep the original process method for backward compatibility
    async def process(self, state: ChatState) -> ChatState:
        """
        Legacy method - delegates to process_entry for backward compatibility
        """
        return await self.process_entry(state)


# Global instance
pastport_chat_manager = PastPortChatManager()
