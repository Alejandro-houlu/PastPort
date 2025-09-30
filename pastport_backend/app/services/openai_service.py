"""
OpenAI GPT-4 Integration Service for PastPort Museum Chat
Handles fallback queries and age-appropriate response personalization
"""
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
import openai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    OpenAI GPT-4 service for museum chat system
    Provides two main functions:
    1. Fallback queries when museum RAG cannot answer
    2. Age-appropriate personalization of responses
    """
    
    def __init__(self, api_key: str = None):
        """Initialize OpenAI service with API key"""
        # Get API key from environment variable or use provided key
        self.api_key = api_key or os.getenv('OPENAI_KEY')
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_KEY environment variable.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Configuration
        self.fallback_model = "gpt-4"
        self.personalization_model = "gpt-4"
        self.max_tokens_fallback = 500
        self.max_tokens_personalization = 600
        
        logger.info("OpenAI Service initialized for museum chat")
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        max_tokens: int = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generic chat completion method for agents to use with their own prompts
        
        Args:
            messages: List of message objects for the conversation
            model: Model to use (defaults to fallback_model)
            max_tokens: Maximum tokens (defaults to fallback max_tokens)
            temperature: Sampling temperature
            
        Returns:
            Dictionary with response content and metadata
        """
        try:
            model = model or self.fallback_model
            max_tokens = max_tokens or self.max_tokens_fallback
            
            logger.info(f"Making OpenAI chat completion with {model}")
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Extract response content
            content = response.choices[0].message.content.strip()
            
            result = {
                "success": True,
                "content": content,
                "metadata": {
                    "model": model,
                    "tokens_used": response.usage.total_tokens,
                    "finish_reason": response.choices[0].finish_reason
                }
            }
            
            logger.info(f"OpenAI chat completion successful (tokens: {response.usage.total_tokens})")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI chat completion failed: {str(e)}")
            return {
                "success": False,
                "content": "I apologize, but I encountered an error processing your request.",
                "error": str(e),
                "metadata": {"error_occurred": True}
            }
    
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check OpenAI service health and connectivity
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Simple test query to verify API connectivity
            test_response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for health check
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "api_accessible": True,
                "model_available": True,
                "test_tokens_used": test_response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e)
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for the OpenAI service
        Note: This is a placeholder for future implementation with usage tracking
        """
        return {
            "service_status": "active",
            "fallback_model": self.fallback_model,
            "personalization_model": self.personalization_model,
            "max_tokens_fallback": self.max_tokens_fallback,
            "max_tokens_personalization": self.max_tokens_personalization
        }


# Global service instance
openai_service = OpenAIService()
