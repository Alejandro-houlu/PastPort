"""
PastPort Chat Manager Agent
Handles query validation, safety checks, and chat history retrieval
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select

from app.services.openai_service import openai_service
from app.services.artifact_cache_service import get_or_refresh_artifacts
from app.services.s3_service import s3_service
from app.models.chat import ChatMessage, ChatSession
from app.models.artifact import Artifact
from app.models.user_click_history import UserClickHistory
from app.database import get_db
from app.dependencies.question_recommender import get_question_recommender
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
    
    def get_artifact_existence_prompt(self, query: str, artifacts: List[str]) -> List[Dict[str, str]]:
        """
        Generate prompt to check if query mentions known artifacts
        
        Args:
            query: User's original query
            artifacts: List of artifact names from database
            
        Returns:
            List of message objects for OpenAI chat completion
        """
        artifacts_list = "\n".join([f"- {artifact}" for artifact in artifacts])
        
        system_prompt = f"""You are a museum assistant checking if a visitor's question is about any of the artifacts in our collection.

Our current artifacts:
{artifacts_list}

Your task:
- Analyze if the user's query is asking about, mentioning, or referring to ANY of these specific artifacts
- Be flexible with names (e.g., "rafflesia" matches "Rafflesia arnoldii" or "corpse flower")
- Consider context and synonyms
- If the query is about general topics that might relate to artifacts but doesn't specifically ask about them, respond NO
- You need to first fix all spelling errors from the user. Then match. E.g. 'Tell me about the saropods in LKC museum', this will match with 'dinosaur_sauropod'

Response format:
- If the query IS about a specific artifact in our list: respond with "YES: artifact_name_here" (use the exact name from the list)
- If the query is NOT about a specific artifact in our list: respond with "NO"

Examples:
- "Tell me about sperm whales" → "YES: sperm_whale"
- "What's in the museum?" → "NO"
- "Info on sauropods" → "YES: dinosaur_sauropod"

Keep your response brief: "YES: artifact_name" or "NO"."""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Is this query about any of our artifacts? Query: '{query}'"}
        ]
    
    def get_validation_with_image_prompt(self, query: str, image_label: str) -> List[Dict[str, str]]:
        """
        Generate prompt for query validation with image context
        
        Args:
            query: User's original query to validate
            image_label: Label from image recognition (e.g., "rafflesia")
            
        Returns:
            List of message objects for OpenAI chat completion
        """
        system_prompt = """You are a museum chat manager responsible for validating and improving user queries.

Your tasks:
1. First, check if the query is appropriate (no offensive/harmful content). If inappropriate, mark is_valid=false and return.
2. Check if the query mentions a SPECIFIC artifact/species name (even if different from the image label).
3. If query is SPECIFIC (mentions an artifact name), keep it as-is. Do NOT rephrase it even if it differs from the image.
4. If query is VAGUE (e.g., "tell me more", "what is this"), rephrase using the image label to add context.

IMPORTANT RULES:
- If user asks about a specific artifact (e.g., "sauropods", "sperm whale"), ALWAYS set is_edited=false
- Only rephrase VAGUE queries that lack specific artifact names
- All appropriate queries should have is_valid=true

VALIDATION CRITERIA:
✅ ACCEPT (is_valid=true): 
- Questions about natural history, science, exhibits, educational content
- Questions mentioning specific artifacts/species (even if different from image)
- General museum questions

❌ REJECT (is_valid=false):
- Offensive language, inappropriate content, spam
- Harmful requests

Response format (JSON):
{
  "is_valid": true/false,
  "rephrased_query": "the rephrased query or original if specific",
  "is_edited": true/false,
  "reason": "brief explanation"
}

Example 1 (VAGUE - needs rephrasing):
Query: "Tell me more"
Image: "rafflesia"
Response: {"is_valid": true, "rephrased_query": "Tell me more about the Rafflesia", "is_edited": true, "reason": "Added image context to vague query"}

Example 2 (SPECIFIC - keep as-is):
Query: "Tell me about sauropods"
Image: "rafflesia"
Response: {"is_valid": true, "rephrased_query": "Tell me about sauropods", "is_edited": false, "reason": "Query already specific"}

Example 3 (SPECIFIC - keep as-is):
Query: "What do sperm whales eat?"
Image: "sperm_whale"
Response: {"is_valid": true, "rephrased_query": "What do sperm whales eat?", "is_edited": false, "reason": "Query already specific"}

Keep response as valid JSON only."""
        
        formatted_label = ' '.join(word.capitalize() for word in image_label.split('_'))
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: '{query}'\nImage Label: '{formatted_label}'"}
        ]
    
    def get_validation_prompt(self, query: str) -> List[Dict[str, str]]:
        """
        Generate prompt for query validation without image context
        
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
    
    async def extract_artifact_from_query(self, query: str) -> Optional[str]:
        """
        Extract artifact name from user query using OpenAI
        Returns artifact name in Title Case format (e.g., "Sperm Whale") or None
        
        Args:
            query: User's original query
            
        Returns:
            Artifact name in Title Case format or None if not found
        """
        try:
            self.logger.info(f"Extracting artifact name from query: '{query[:50]}...'")
            
            system_prompt = """You are a museum assistant that extracts artifact/species names from visitor questions.

Your task:
- Analyze the user's query and identify what artifact or species they are asking about
- Return ONLY the artifact/species name
- Format the name in Title Case with spaces (e.g., "Sperm Whale", "Rafflesia Arnoldii", "Dinosaur Sauropod")
- Fix any spelling errors in the artifact name
- If the query doesn't clearly mention a specific artifact, return "NONE"

Examples:
- "Tell me about sperm whales" → "Sperm Whale"
- "What do sauropods eat?" → "Dinosaur Sauropod"
- "Info on rafflesia" → "Rafflesia Arnoldii"
- "What's in this museum?" → "NONE"

Keep your response to ONLY the artifact name or "NONE"."""
            
            extraction_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract artifact name: '{query}'"}
            ]
            
            result = await openai_service.chat_completion(
                messages=extraction_messages,
                model="gpt-3.5-turbo",
                max_tokens=30,
                temperature=0.2
            )
            
            if result['success']:
                artifact_name = result['content'].strip()
                if artifact_name.upper() == "NONE":
                    self.logger.info("No artifact name found in query")
                    return None
                else:
                    self.logger.info(f"Extracted artifact name: {artifact_name}")
                    return artifact_name
            else:
                self.logger.warning(f"Artifact extraction failed: {result.get('error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting artifact from query: {e}", exc_info=True)
            return None
    
    async def record_artifact_click(self, user_id: str, artifact_name: str) -> bool:
        """
        Record a user click on an artifact (from chat query)
        
        Args:
            user_id: User ID
            artifact_name: Artifact name in database format
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Recording click for user {user_id} on artifact {artifact_name}")
            
            async for db in get_db():
                # Get artifact ID
                result = await db.execute(
                    select(Artifact).filter(Artifact.artifact_name == artifact_name)
                )
                artifact = result.scalar_one_or_none()
                
                if not artifact:
                    self.logger.warning(f"Artifact {artifact_name} not found for click recording")
                    return False
                
                # Check if user already has a click record
                result = await db.execute(
                    select(UserClickHistory).filter(
                        UserClickHistory.user_id == user_id,
                        UserClickHistory.artifact_id == artifact.id
                    )
                )
                existing_click = result.scalar_one_or_none()
                
                if existing_click:
                    # Update timestamp
                    existing_click.clicked_at = datetime.now(ZoneInfo("Asia/Singapore"))
                    existing_click.source = "chat_query"
                    await db.commit()
                    self.logger.info(f"Updated click timestamp for artifact {artifact_name}")
                else:
                    # Create new click record
                    new_click = UserClickHistory(
                        user_id=user_id,
                        artifact_id=artifact.id,
                        source="chat_query"
                    )
                    db.add(new_click)
                    await db.commit()
                    self.logger.info(f"Recorded new click for artifact {artifact_name}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error recording artifact click: {e}", exc_info=True)
            return False
    
    async def get_question_recommendations(self, artifact_name: str, user_query: str) -> Optional[Dict[str, Any]]:
        """
        Get question recommendations from the recommender service
        
        Args:
            artifact_name: Name of the artifact in Title Case format
            user_query: User's original query
            
        Returns:
            Dictionary with recommendations or None if failed
        """
        try:
            self.logger.info(f"Getting recommendations for artifact: {artifact_name}")
            
            # Get the recommender service
            recommender_service = get_question_recommender()
            
            # Get recommendations
            recommendations = recommender_service.get_recommendations(
                species=artifact_name,
                question=user_query
            )
            
            if recommendations:
                self.logger.info(f"Successfully retrieved recommendations for {artifact_name}")
                return {
                    "success": True,
                    "artifact_name": artifact_name,
                    "questions": recommendations
                }
            else:
                self.logger.warning(f"No recommendations returned for {artifact_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting question recommendations: {e}", exc_info=True)
            return None
    
    async def fetch_artifact_with_images(self, artifact_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch artifact data from database with S3 image URLs
        Similar to artifacts_api.py but for internal use
        
        Args:
            artifact_name: Name of the artifact in database format (e.g., 'sperm_whale')
            
        Returns:
            Dictionary with artifact data and image URL or None if failed
        """
        try:
            self.logger.info(f"Fetching artifact data with images for: {artifact_name}")
            
            # Import required modules
            from sqlalchemy import select
            from app.models.artifact import Artifact
            from app.database import get_db
            from app.services.s3_service import s3_service
            
            # Query artifact from database
            async for db in get_db():
                result = await db.execute(
                    select(Artifact).filter(Artifact.artifact_name == artifact_name)
                )
                artifact = result.scalar_one_or_none()
                
                if not artifact:
                    self.logger.warning(f"Artifact not found in database: {artifact_name}")
                    return None
                
                # Convert artifact to dictionary
                artifact_data = artifact.to_dict()
                
                # Handle datetime serialization
                if artifact_data.get('created_at'):
                    artifact_data['created_at'] = artifact_data['created_at'].isoformat()
                if artifact_data.get('updated_at'):
                    artifact_data['updated_at'] = artifact_data['updated_at'].isoformat()
                if artifact_data.get('display_startDate'):
                    artifact_data['display_startDate'] = artifact_data['display_startDate'].isoformat()
                
                # Construct S3 folder path
                folder_path = f"pastport/artifact_images/{artifact_name}_{artifact.id}/"
                self.logger.info(f"Looking for images in S3 folder: {folder_path}")
                
                # Get first image from S3
                first_image_key = s3_service.get_first_image(folder_path)
                
                if first_image_key:
                    # Generate presigned URL (valid for 1 hour)
                    presigned_url = s3_service.generate_presigned_url(first_image_key, expiration=3600)
                    
                    if presigned_url:
                        artifact_data['image_url'] = presigned_url
                        artifact_data['image_key'] = first_image_key
                        self.logger.info(f"Successfully generated presigned URL for {artifact_name}")
                    else:
                        artifact_data['image_url'] = None
                        artifact_data['image_key'] = None
                        self.logger.warning(f"Failed to generate presigned URL for {artifact_name}")
                else:
                    artifact_data['image_url'] = None
                    artifact_data['image_key'] = None
                    self.logger.warning(f"No images found for {artifact_name} in S3")
                
                return artifact_data
                
        except Exception as e:
            self.logger.error(f"Error fetching artifact with images: {e}", exc_info=True)
            return None
    
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
            
            # Check if we have image_result that could provide context
            image_result = state.get('image_result')
            has_image_label = bool(image_result and image_result.get('label'))
            
            if has_image_label:
                # Use validation with image context
                image_label = image_result['label']
                self.logger.info(f"Validating with image context. Label: {image_label}")
                
                validation_messages = self.get_validation_with_image_prompt(
                    state['original_query'],
                    image_label
                )
                
                validation_result = await openai_service.chat_completion(
                    messages=validation_messages,
                    model="gpt-3.5-turbo",
                    max_tokens=150,
                    temperature=0.3
                )
                
                if not validation_result['success']:
                    error_msg = f"Query validation failed: {validation_result.get('error')}"
                    self.logger.error(error_msg)
                    state['error'] = error_msg
                    state['success'] = False
                    return state
                
                # Parse JSON response
                try:
                    validation_data = json.loads(validation_result['content'].strip())
                    is_valid = validation_data.get('is_valid', False)
                    rephrased_query = validation_data.get('rephrased_query', state['original_query'])
                    is_edited = validation_data.get('is_edited', False)
                    reason = validation_data.get('reason', '')
                    
                    self.logger.info(f"Validation result: is_valid={is_valid}, is_edited={is_edited}, reason={reason}")
                    
                    if is_edited:
                        self.logger.info(f"Query rephrased: '{state['original_query']}' → '{rephrased_query}'")
                        state['original_query'] = rephrased_query
                    
                    validation_response = f"VALID (with image context, edited={is_edited})" if is_valid else f"INVALID: {reason}"
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse validation JSON: {e}. Response: {validation_result['content']}")
                    error_msg = f"Validation failed: Invalid JSON response from LLM"
                    state['error'] = error_msg
                    state['success'] = False
                    return state
                
            else:
                # Normal validation without image context
                validation_messages = self.get_validation_prompt(state['original_query'])
                
                validation_result = await openai_service.chat_completion(
                    messages=validation_messages,
                    model="gpt-3.5-turbo",
                    max_tokens=50,
                    temperature=0.3
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
            
            # Check if query was rejected
            if not is_valid:
                error_msg = f"Query rejected during validation: {validation_response}"
                self.logger.warning(error_msg)
                state['error'] = error_msg
                state['success'] = False
                return state
            
            # Step 1A: Check artifact cache and get artifact list
            self.logger.info("Checking artifact cache")
            artifacts = await get_or_refresh_artifacts()
            
            # Step 1B: Check if query mentions known artifacts
            is_artifact_exist = False
            if artifacts:
                self.logger.info(f"Checking if query mentions any of {len(artifacts)} known artifacts")
                
                artifact_check_messages = self.get_artifact_existence_prompt(
                    state['original_query'],
                    artifacts
                )
                
                artifact_check_result = await openai_service.chat_completion(
                    messages=artifact_check_messages,
                    model="gpt-3.5-turbo",
                    max_tokens=10,
                    temperature=0.2
                )
                
                if artifact_check_result['success']:
                    artifact_response = artifact_check_result['content'].strip()
                    # Parse response: "YES: artifact_name" or "NO"
                    if artifact_response.upper().startswith("YES"):
                        is_artifact_exist = True
                        # Extract artifact name from response
                        if ":" in artifact_response:
                            artifact_name = artifact_response.split(":", 1)[1].strip()
                            state['artifact_name'] = artifact_name
                            self.logger.info(f"Artifact found: {artifact_name}")
                        else:
                            state['artifact_name'] = None
                            self.logger.warning("Artifact exists but name not provided in response")
                    else:
                        is_artifact_exist = False
                        state['artifact_name'] = None
                    self.logger.info(f"Artifact existence check: {artifact_response}")
                else:
                    self.logger.warning("Artifact existence check failed, defaulting to False")
                    state['artifact_name'] = None
            else:
                self.logger.warning("No artifacts in cache, skipping artifact existence check")
                state['artifact_name'] = None
            
            # Store artifact existence flag in state
            state['is_artifact_exist'] = is_artifact_exist
            
            # Step 1C: Determine if we need to fetch artifact data for header update
            if is_artifact_exist and state.get('artifact_name'):
                # Artifact found in query - check if it differs from current image context
                # current_image_label = state.get('image_result', {}).get('label')
                current_image_label = (state.get("image_result") or {}).get("label")

                
                if current_image_label and current_image_label == state['artifact_name']:
                    # Same artifact as current context - no header update needed
                    self.logger.info(f"Query artifact matches image context: {current_image_label} - no header update needed")
                    state['artifact_data'] = None
                else:
                    # Different artifact or no image context - fetch full artifact data
                    self.logger.info(f"Fetching artifact data for header update. Query artifact: {state['artifact_name']}, Image context: {current_image_label}")
                    artifact_data = await self.fetch_artifact_with_images(state['artifact_name'])
                    
                    if artifact_data:
                        state['artifact_data'] = artifact_data
                        self.logger.info(f"Successfully fetched artifact data for {state['artifact_name']}")
                        
                        # Record this as a user click since they queried a different artifact
                        await self.record_artifact_click(state['user_id'], state['artifact_name'])
                    else:
                        state['artifact_data'] = None
                        self.logger.warning(f"Failed to fetch artifact data for {state['artifact_name']}")
            else:
                # General question (no artifact in database) - signal to hide header
                self.logger.info("General question detected - signaling to hide artifact header")
                state['artifact_data'] = {"is_general_question": True}
            
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
            
            # Generate question recommendations if artifact exists
            if state.get('is_artifact_exist') and state.get('artifact_name'):
                self.logger.info(f"Artifact exists: {state['artifact_name']} - generating question recommendations")
                try:
                    # Format artifact name from database format to Title Case
                    # e.g., "sperm_whale" -> "Sperm Whale"
                    db_artifact_name = state['artifact_name']
                    formatted_artifact_name = ' '.join(word.capitalize() for word in db_artifact_name.split('_'))
                    self.logger.info(f"Formatted artifact name: {db_artifact_name} -> {formatted_artifact_name}")
                    
                    # Get recommendations using formatted name and original query
                    recommendations = await self.get_question_recommendations(
                        formatted_artifact_name, 
                        state['original_query']
                    )
                    
                    if recommendations:
                        state['recommended_questions'] = recommendations
                        self.logger.info(f"Successfully generated recommendations for {formatted_artifact_name}")
                    else:
                        self.logger.warning("Failed to generate recommendations")
                        state['recommended_questions'] = None
                        
                except Exception as e:
                    self.logger.error(f"Error generating recommendations: {e}", exc_info=True)
                    state['recommended_questions'] = None
            else:
                self.logger.info("No artifact in query - skipping recommendations")
                state['recommended_questions'] = None
            
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
