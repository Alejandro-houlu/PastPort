"""
LangGraph Agent for Museum RAG System
Handles query processing, rephrasing, and response formatting
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from app.dependencies.rag import get_query_engine, get_rag_status
from pastport_museum_rag.core.query_engine import QueryResult

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent processing states"""
    INITIAL = "initial"
    ANALYZING = "analyzing"
    QUERYING = "querying"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class AgentContext:
    """Context object passed between agent nodes"""
    original_query: str
    processed_query: Optional[str] = None
    rag_result: Optional[QueryResult] = None
    final_response: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    state: AgentState = AgentState.INITIAL
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    max_results: int = 5


class MuseumAgent:
    """
    LangGraph-style agent for processing museum queries
    
    This agent follows a simple workflow:
    1. Analyze the query
    2. Process/rephrase if needed
    3. Query the RAG system
    4. Format the response
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MuseumAgent")
    
    async def process_query(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Main entry point for processing a query through the agent workflow
        
        Args:
            query: User's original query
            max_results: Maximum number of sources to retrieve
            
        Returns:
            Dictionary with processed response and metadata
        """
        context = AgentContext(
            original_query=query,
            max_results=max_results,
            metadata={}
        )
        
        try:
            # Execute agent workflow
            context = await self._analyze_query_node(context)
            if context.state == AgentState.ERROR:
                return self._format_error_response(context)
            
            context = await self._query_rag_node(context)
            if context.state == AgentState.ERROR:
                return self._format_error_response(context)
            
            context = await self._format_response_node(context)
            if context.state == AgentState.ERROR:
                return self._format_error_response(context)
            
            return self._format_success_response(context)
            
        except Exception as e:
            self.logger.error(f"Agent workflow error: {e}", exc_info=True)
            context.state = AgentState.ERROR
            context.error_message = f"Agent processing failed: {str(e)}"
            return self._format_error_response(context)
    
    async def _analyze_query_node(self, context: AgentContext) -> AgentContext:
        """
        Node 1: Analyze and potentially rephrase the query
        
        For now, this is a simple pass-through, but can be extended to:
        - Detect query intent
        - Rephrase for better RAG retrieval
        - Add context from conversation history
        """
        self.logger.info(f"Analyzing query: '{context.original_query[:50]}...'")
        
        try:
            context.state = AgentState.ANALYZING
            
            # Simple analysis - just use the original query
            # In the future, this could use an LLM to rephrase or enhance the query
            context.processed_query = context.original_query.strip()
            
            # Add some basic metadata
            context.metadata.update({
                "query_length": len(context.original_query),
                "query_words": len(context.original_query.split()),
                "analysis_performed": True
            })
            
            self.logger.info("Query analysis completed")
            return context
            
        except Exception as e:
            self.logger.error(f"Query analysis failed: {e}")
            context.state = AgentState.ERROR
            context.error_message = f"Query analysis failed: {str(e)}"
            return context
    
    async def _query_rag_node(self, context: AgentContext) -> AgentContext:
        """
        Node 2: Query the RAG system with the processed query
        """
        self.logger.info(f"Querying RAG system with: '{context.processed_query[:50]}...'")
        
        try:
            context.state = AgentState.QUERYING
            
            # Check RAG system status
            rag_status = get_rag_status()
            if rag_status["status"] != "ready":
                raise Exception(f"RAG system not ready: {rag_status.get('error', 'Unknown error')}")
            
            # Get query engine and execute query
            query_engine = get_query_engine()
            context.rag_result = query_engine.query(
                context.processed_query, 
                k=context.max_results
            )
            
            # Update metadata
            context.metadata.update({
                "sources_retrieved": len(context.rag_result.contexts),
                "response_length": len(context.rag_result.answer),
                "rag_query_successful": True
            })
            
            self.logger.info(f"RAG query completed - {len(context.rag_result.contexts)} sources retrieved")
            return context
            
        except Exception as e:
            self.logger.error(f"RAG query failed: {e}")
            context.state = AgentState.ERROR
            context.error_message = f"RAG query failed: {str(e)}"
            return context
    
    async def _format_response_node(self, context: AgentContext) -> AgentContext:
        """
        Node 3: Format the final response for the user
        
        This node can be extended to:
        - Post-process the RAG response
        - Add conversational elements
        - Format for specific output channels
        """
        self.logger.info("Formatting final response")
        
        try:
            context.state = AgentState.PROCESSING
            
            if not context.rag_result:
                raise Exception("No RAG result to format")
            
            # For now, use the RAG response directly
            # In the future, this could enhance the response with additional context
            context.final_response = context.rag_result.answer
            
            # Format sources for frontend consumption
            context.sources = []
            for source_context in context.rag_result.contexts:
                formatted_source = {
                    "content": f"Source: {source_context.get('source', 'unknown')}",
                    "metadata": source_context.get('metadata', {}),
                    "relevance_score": source_context.get('score', 0.0),
                    "id": source_context.get('id', 'unknown')
                }
                context.sources.append(formatted_source)
            
            # Update metadata
            context.metadata.update({
                "final_response_length": len(context.final_response),
                "sources_formatted": len(context.sources),
                "formatting_completed": True
            })
            
            context.state = AgentState.COMPLETE
            self.logger.info("Response formatting completed")
            return context
            
        except Exception as e:
            self.logger.error(f"Response formatting failed: {e}")
            context.state = AgentState.ERROR
            context.error_message = f"Response formatting failed: {str(e)}"
            return context
    
    def _format_success_response(self, context: AgentContext) -> Dict[str, Any]:
        """Format successful agent response"""
        return {
            "success": True,
            "response": context.final_response,
            "sources": context.sources,
            "metadata": {
                **context.metadata,
                "original_query": context.original_query,
                "processed_query": context.processed_query,
                "agent_state": context.state.value
            }
        }
    
    def _format_error_response(self, context: AgentContext) -> Dict[str, Any]:
        """Format error response"""
        return {
            "success": False,
            "error": context.error_message,
            "response": "I apologize, but I encountered an error while processing your query. Please try again or contact support if the issue persists.",
            "sources": [],
            "metadata": {
                **context.metadata,
                "original_query": context.original_query,
                "agent_state": context.state.value,
                "error_occurred": True
            }
        }


# Global agent instance
museum_agent = MuseumAgent()


async def process_museum_query(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Convenience function to process a museum query through the agent
    
    Args:
        query: User's query
        max_results: Maximum number of sources to retrieve
        
    Returns:
        Processed response dictionary
    """
    return await museum_agent.process_query(query, max_results)
