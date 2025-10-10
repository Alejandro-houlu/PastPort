"""
Museum Query Agent
Handles RAG querying with OpenAI GPT-4 fallback for museum content
"""
import logging
from typing import Dict, Any, List, Optional

from app.services.openai_service import openai_service
from app.dependencies.rag import get_query_engine, get_rag_status
from .state import ChatState

logger = logging.getLogger(__name__)


class MuseumQueryAgent:
    """
    Museum Query Agent for PastPort Museum Chat System
    
    Responsibilities:
    - Query rephrasing for better RAG search
    - Querying museum RAG system
    - Fallback to OpenAI GPT-4 when museum knowledge is insufficient
    - Response quality assessment
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MuseumQueryAgent")
    
    def get_query_rephrase_prompt(self, query: str, image_result: Optional[Dict] = None) -> List[Dict[str, str]]:
        """
        Generate prompt for query rephrasing to improve RAG search
        
        Args:
            query: Original user query
            image_result: Optional image recognition context
            
        Returns:
            List of message objects for OpenAI chat completion
        """
        system_prompt = """You are a museum query processor. Your job is to rephrase user questions to be more effective for searching a museum's knowledge base.

Guidelines for rephrasing:
- Make queries more specific and search-friendly
- Include relevant keywords about natural history, species, exhibits, fossils
- Keep the original intent but make it clearer and more searchable
- Add scientific names or terms when appropriate
- Focus on factual, educational content
- If an image was recognized, incorporate that context naturally

Examples:
- "What's that big dinosaur?" → "Information about large dinosaur species sauropod exhibits"
- "Tell me about flowers" → "Botanical specimens flowering plants exhibits information"
- "How old is this?" → "Age dating geological specimens fossil dating methods"

Keep responses brief and focused on search optimization."""
        
        user_content = f"Original user query: '{query}'"
        user_content += "\n\nProvide a rephrased query optimized for museum database search:"
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    def get_fallback_prompt(self, query: str, image_result: Optional[Dict] = None) -> List[Dict[str, str]]:
        """
        Generate prompt for OpenAI fallback when RAG system cannot answer
        
        Args:
            query: Original user query
            image_result: Optional image recognition context
            
        Returns:
            List of message objects for OpenAI chat completion
        """
        system_prompt = """You are a knowledgeable assistant helping visitors to a natural history museum. 
The museum's knowledge base couldn't answer the user's question, so you're providing general educational information.

IMPORTANT GUIDELINES:
- Provide accurate, educational information about natural history and science
- Keep responses informative but concise (under 400 words)
- Focus on natural history, science, paleontology, biology, geology, and educational content
- Be engaging and educational for museum visitors of all ages
- If asked about specific museum exhibits, politely explain you don't have access to current museum information
- Include interesting facts that would enhance a museum visit
- Maintain scientific accuracy

RESPONSE STRUCTURE:
1. Answer the question with general knowledge
2. Include 2-3 interesting related facts
3. If relevant, mention what types of exhibits or specimens might relate to this topic
4. Keep response with 100 words

Remember: This is general knowledge, not specific to any particular museum's collection."""
        
        user_content = query
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    def is_meaningful_response(self, response: str) -> bool:
        """
        Check if RAG response is meaningful and useful
        
        Args:
            response: RAG system response to evaluate
            
        Returns:
            Boolean indicating if response is meaningful
        """
        if not response or len(response.strip()) < 20:
            return False
        
        # Check for common "I don't know" patterns
        low_quality_phrases = [
            "i don't know",
            "no information",
            "cannot find",
            "unable to provide",
            "not available",
            "insufficient information",
            "i'm not sure",
            "i don't have"
        ]
        
        response_lower = response.lower()
        for phrase in low_quality_phrases:
            if phrase in response_lower:
                return False
        
        # Check if response has substantial content
        words = response.split()
        if len(words) < 10:  # Very short responses likely not helpful
            return False
        
        return True
    
    async def process(self, state: ChatState) -> ChatState:
        """
        Main processing method for the Museum Query Agent
        
        Args:
            state: Current chat state object
            
        Returns:
            Updated chat state after museum query processing
        """
        self.logger.info(f"Museum Query Agent processing: '{state['original_query'][:50]}...'")
        
        try:
            # Send thinking update to WebSocket
            if state.get('websocket_callback'):
                await state['websocket_callback']({
                    "type": "thinking",
                    "content": "Searching museum knowledge base...",
                    "stage": "museum_query",
                    "session_id": state['session_id'],
                    "message_id": state['message_id']
                })
            
            # Step 1: Rephrase query for better RAG search
            self.logger.info("Rephrasing query for RAG optimization")
            rephrase_messages = self.get_query_rephrase_prompt(
                state['original_query'], 
                state.get('image_result')
            )
            
            rephrase_result = await openai_service.chat_completion(
                messages=rephrase_messages,
                model="gpt-3.5-turbo",
                max_tokens=100,
                temperature=0.3
            )
            
            if rephrase_result['success']:
                search_query = rephrase_result['content'].strip()
                self.logger.info(f"Query rephrased to: '{search_query}'")
            else:
                search_query = state['original_query']  # Fallback to original
                self.logger.warning("Query rephrasing failed, using original query")
            
            # Step 2: Check if query is about known artifacts BEFORE trying RAG
            # If query is valid but not about our artifacts, skip RAG entirely
            rag_success = False
            rag_response = None
            contexts = []
            
            if (not state.get('is_artifact_exist') and 
                state.get('manager_validation', {}).get('is_valid')):
                self.logger.info("Query not about museum artifacts, skipping RAG and using GPT-4 directly")
                
                # Update thinking status
                if state.get('websocket_callback'):
                    await state['websocket_callback']({
                        "type": "thinking",
                        "content": "This question is not about our specific artifacts. Searching general knowledge...",
                        "stage": "general_search",
                        "session_id": state['session_id'],
                        "message_id": state['message_id']
                    })
                
                # Skip RAG, will go directly to GPT-4 fallback below
                rag_success = False
                
            else:
                # Step 3: Query the museum RAG system (only if query might be about artifacts)
                try:
                    self.logger.info("Querying museum RAG system")
                    
                    # Check RAG system status
                    rag_status = get_rag_status()
                    if rag_status["status"] != "ready":
                        raise Exception(f"RAG system not ready: {rag_status.get('error', 'Unknown error')}")
                    
                    # Execute RAG query
                    query_engine = get_query_engine()
                    rag_result = query_engine.query(search_query, k=5)
                    
                    self.logger.info(f"RAG query executed, response length: {len(rag_result.answer) if rag_result.answer else 0}")
                    
                    # Evaluate response quality
                    if (rag_result.answer and 
                        self.is_meaningful_response(rag_result.answer)):
                        rag_success = True
                        rag_response = rag_result.answer
                        contexts = rag_result.contexts or []
                        self.logger.info(f"RAG query successful with {len(contexts)} contexts")
                    else:
                        self.logger.info("RAG returned insufficient answer, will use OpenAI fallback")
                        
                except Exception as e:
                    self.logger.error(f"RAG query failed: {str(e)}")
                    # Continue to fallback - this is expected behavior
            
            # Step 4: Use OpenAI GPT-4 fallback if RAG was skipped or failed
            if not rag_success:
                self.logger.info("Using OpenAI GPT-4 fallback")
                
                # Update thinking status (only if not already set above)
                if state.get('is_artifact_exist') and state.get('websocket_callback'):
                    await state['websocket_callback']({
                        "type": "thinking",
                        "content": "Museum database didn't have specific info, searching general knowledge...",
                        "stage": "fallback_search",
                        "session_id": state['session_id'],
                        "message_id": state['message_id']
                    })
                
                fallback_messages = self.get_fallback_prompt(
                    state['original_query'],
                    state.get('image_result')
                )
                
                fallback_result = await openai_service.chat_completion(
                    messages=fallback_messages,
                    model="gpt-4",  # Use GPT-4 for better quality fallback
                    max_tokens=500,
                    temperature=0.7
                )
                
                if fallback_result['success']:
                    final_response = fallback_result['content']
                    response_source = "openai_web"
                    contexts = []
                    self.logger.info("OpenAI fallback successful")
                else:
                    final_response = "I apologize, but I'm unable to provide information about that topic right now. Please try asking a different question or speak with museum staff for assistance."
                    response_source = "error_fallback"
                    contexts = []
                    self.logger.error("Both RAG and OpenAI fallback failed")
            else:
                final_response = rag_response
                response_source = "museum_rag"
            
            # Step 4: Store museum query results
            state['museum_response'] = {
                "response": final_response,
                "source": response_source,
                "contexts": contexts,
                "rag_success": rag_success,
                "rephrased_query": search_query,
                "context_count": len(contexts)
            }
            
            state['processing_stage'] = "museum_queried"
            
            self.logger.info(
                f"Museum Query processing completed. "
                f"Source: {response_source}, RAG success: {rag_success}, "
                f"Contexts: {len(contexts)}"
            )
            
            return state
            
        except Exception as e:
            error_msg = f"Museum Query Agent processing failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            state['error'] = error_msg
            state['success'] = False
            return state


# Global instance
museum_query_agent = MuseumQueryAgent()
