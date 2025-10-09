"""
Communications Agent
Handles age-appropriate response personalization and database persistence
"""
import logging
from typing import Dict, Any, List, Optional

from app.services.openai_service import openai_service
from .state import ChatState
from app.models.chat import ChatSession, ChatMessage
from app.database import get_db

logger = logging.getLogger(__name__)


class CommsAgent:
    """
    Communications Agent for PastPort Museum Chat System
    
    Responsibilities:
    - Age-appropriate personalization of responses
    - Chat history context integration
    - Database persistence of conversations
    - Final response formatting
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CommsAgent")
    
    def get_age_guidelines(self, age_group: str) -> Dict[str, str]:
        """
        Get personalization guidelines for specific age group
        
        Args:
            age_group: Target age group (child, teen, adult, senior)
            
        Returns:
            Dictionary with personalization guidelines
        """
        age_guidelines = {
            "child": {
                "tone": "friendly, enthusiastic, encouraging",
                "vocabulary": "simple words, avoid jargon",
                "length": "shorter, bite-sized information",
                "engagement": "use fun facts, comparisons to familiar things",
                "emojis": "appropriate use of emojis to make it fun",
                "structure": "short paragraphs with clear, simple sentences"
            },
            "teen": {
                "tone": "engaging, educational, slightly casual",
                "vocabulary": "age-appropriate, educational terms with explanations",
                "length": "moderate detail with interesting facts",
                "engagement": "cool facts, connections to modern world",
                "emojis": "occasional relevant emojis",
                "structure": "informative but not overwhelming, include 'did you know' style facts"
            },
            "adult": {
                "tone": "informative, professional, comprehensive",
                "vocabulary": "full vocabulary, scientific terms explained",
                "length": "detailed information with context",
                "engagement": "scientific accuracy, broader connections",
                "emojis": "minimal, professional use",
                "structure": "well-organized, comprehensive explanations"
            },
            "senior": {
                "tone": "respectful, clear, well-structured",
                "vocabulary": "clear explanations, avoid too much jargon",
                "length": "comprehensive but well-organized",
                "engagement": "historical context, broader perspective",
                "emojis": "very minimal, formal approach",
                "structure": "clear headings, methodical presentation"
            }
        }
        
        return age_guidelines.get(age_group, age_guidelines["adult"])
    
    def get_personalization_prompt(
        self, 
        response: str, 
        age_group: str, 
        chat_history: List[Dict], 
        original_query: str
    ) -> List[Dict[str, str]]:
        """
        Generate prompt for age-appropriate personalization
        
        Args:
            response: Original museum response to personalize
            age_group: Target age group for personalization
            chat_history: Recent chat messages for context
            original_query: User's original question
            
        Returns:
            List of message objects for OpenAI chat completion
        """
        guidelines = self.get_age_guidelines(age_group)
        
        system_prompt = f"""You are personalizing museum information for a {age_group} visitor at a natural history museum.

PERSONALIZATION GUIDELINES for {age_group.upper()}:
- Tone: {guidelines['tone']}
- Vocabulary: {guidelines['vocabulary']}
- Length: {guidelines['length']}
- Engagement: {guidelines['engagement']}
- Emojis: {guidelines['emojis']}
- Structure: {guidelines['structure']}

CRITICAL RULES:
✅ DO:
- Maintain all factual accuracy from the original response
- Keep all specific museum information and citations intact
- Preserve any source attributions (like "🌐 From general knowledge")
- Only adjust language style, tone, and presentation
- Consider the conversation history to make responses feel connected
- Make the information accessible and engaging for the target age group

❌ DON'T:
- Add information not in the original response
- Remove important factual details
- Change scientific accuracy
- Ignore previous conversation context

Your goal is to make the information accessible and engaging for a {age_group} while maintaining educational value and accuracy."""
        
        user_content = f"Original museum response to personalize:\n\n{response}"
        
        # Add chat history context if available
        if chat_history and len(chat_history) > 0:
            history_context = "\n\nRecent conversation context:\n"
            for i, msg in enumerate(chat_history[-3:], 1):  # Last 3 messages for context
                history_context += f"{i}. User asked: {msg.get('user_query', '')}\n"
                history_context += f"   Assistant replied: {msg.get('museum_response', '')[:100]}...\n\n"
            user_content += history_context
            user_content += "Note: Use this conversation history to make your response feel naturally connected to the ongoing conversation."
        
        user_content += f"\n\nUser's current question: {original_query}"
        user_content += f"\n\nPersonalize this response appropriately for a {age_group}:"
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    async def save_conversation_to_database(self, state: ChatState) -> bool:
        """
        Save the conversation to database for future reference
        
        Args:
            state: Current chat state with conversation details
            
        Returns:
            Boolean indicating success of database save operation
        """
        try:

            self.logger.info(f"Saving conversation to database for session {state['session_id']}")
            
            async for db in get_db():
                from sqlalchemy import select
                
                # Ensure session exists
                session_stmt = select(ChatSession).where(
                    ChatSession.id == state['session_id'],
                    ChatSession.user_id == state['user_id']
                )
                session_result = await db.execute(session_stmt)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    self.logger.info(f"Creating new chat session: {state['session_id']}")
                    session = ChatSession(
                        id=state['session_id'],
                        user_id=state['user_id'],
                        session_metadata={
                            "user_age_group": state.get('user_age_group'),
                            "created_via": "museum_chat"
                        }
                    )
                    db.add(session)
                
                # Create message record
                message = ChatMessage(
                    id=state['message_id'],
                    chat_session_id=state['session_id'],
                    user_query=state['original_query'],
                    museum_response=state['final_response'],
                    response_source=state['response_source'],
                    user_age_group=state.get('user_age_group'),
                    contexts=state['contexts'],
                    image_result=state.get('image_result'),
                    processing_metadata=state['processing_metadata']
                )
                db.add(message)
                
                # Commit the transaction
                await db.commit()
                
                self.logger.info(f"Successfully saved conversation to database")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to save conversation to database: {str(e)}", exc_info=True)
            return False  # Don't fail the entire process if DB save fails
    
    async def process(self, state: ChatState) -> ChatState:
        """
        Main processing method for the Communications Agent
        
        Args:
            state: Current chat state object
            
        Returns:
            Updated chat state after communication processing
        """
        self.logger.info(f"Comms Agent personalizing for: {state.get('user_age_group', 'adult')}")
        
        try:
            # Send thinking update to WebSocket
            if state.get('websocket_callback'):
                await state['websocket_callback']({
                    "type": "thinking",
                    "content": "Tailoring response for your age group...",
                    "stage": "personalization",
                    "session_id": state['session_id'],
                    "message_id": state['message_id']
                })
            
            museum_response = state['museum_response']
            age_group = state.get('user_age_group', 'adult')
            
            self.logger.info(f"Personalizing response for {age_group} (original length: {len(museum_response['response'])} chars)")
            
            # Step 1: Personalize the response using OpenAI
            personalization_messages = self.get_personalization_prompt(
                museum_response['response'],
                age_group,
                state['chat_history'],
                state['original_query']
            )
            
            personalization_result = await openai_service.chat_completion(
                messages=personalization_messages,
                model="gpt-4",  # Use GPT-4 for better personalization quality
                max_tokens=600,
                temperature=0.3  # Lower temperature for consistency
            )
            
            if personalization_result['success']:
                personalized_content = personalization_result['content']
                source = f"{museum_response['source']}_personalized"
                personalization_success = True
                self.logger.info(f"Personalization successful (new length: {len(personalized_content)} chars)")
            else:
                # Fallback to original response if personalization fails
                self.logger.warning("Personalization failed, using original response")
                personalized_content = museum_response['response']
                source = museum_response['source']
                personalization_success = False
            
            # Step 2: Prepare final response data
            state['comms_response'] = {
                "personalized_response": personalized_content,
                "age_group": age_group,
                "personalization_success": personalization_success,
                "original_length": len(museum_response['response']),
                "personalized_length": len(personalized_content)
            }
            
            # Step 3: Set final state values
            state['final_response'] = personalized_content
            state['response_source'] = source
            state['contexts'] = museum_response['contexts']
            state['processing_metadata'] = {
                "manager_validation": state.get('manager_validation', {}),
                "museum_query": {
                    "source": museum_response['source'],
                    "rag_success": museum_response['rag_success'],
                    "rephrased_query": museum_response['rephrased_query'],
                    "context_count": len(museum_response['contexts'])
                },
                "personalization": {
                    "age_group": age_group,
                    "success": personalization_success,
                    "tokens_used": personalization_result.get('metadata', {}).get('tokens_used', 0)
                }
            }
            
            # Step 4: Save conversation to database
            self.logger.info("Saving conversation to database")
            db_save_success = await self.save_conversation_to_database(state)
            state['processing_metadata']['database_saved'] = db_save_success
            
            # Step 5: Mark processing as completed
            state['processing_stage'] = "completed"
            state['success'] = True
            
            self.logger.info(
                f"Comms Agent processing completed successfully. "
                f"Age group: {age_group}, Personalization: {personalization_success}, "
                f"DB save: {db_save_success}"
            )
            
            return state
            
        except Exception as e:
            error_msg = f"Communications Agent processing failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            state['error'] = error_msg
            state['success'] = False
            return state


# Global instance
comms_agent = CommsAgent()
