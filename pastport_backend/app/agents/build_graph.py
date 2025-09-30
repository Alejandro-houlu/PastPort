"""
LangGraph Build Graph for PastPort Museum Chat System
Orchestrates the three-agent flow: Manager -> Museum Query -> Comms -> END
"""
import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from .state import ChatState
from .pastport_chat_manager import pastport_chat_manager
from .museum_query_agent import museum_query_agent
from .comms_agent import comms_agent

logger = logging.getLogger(__name__)


def should_continue_from_manager(state: ChatState) -> str:
    """
    Determine next step after Manager Agent processing
    
    Args:
        state: Current chat state
        
    Returns:
        Next node name or END
    """
    if state.get('success', True) and not state.get('error'):
        logger.info("Manager validation successful, proceeding to Museum Query Agent")
        return "museum_query"
    else:
        error_msg = state.get('error', 'Unknown validation error')
        logger.warning(f"Manager validation failed: {error_msg}")
        return END


def should_continue_from_museum(state: ChatState) -> str:
    """
    Determine next step after Museum Query Agent processing
    
    Args:
        state: Current chat state
        
    Returns:
        Next node name or END
    """
    if state.get('success', True) and not state.get('error'):
        logger.info("Museum query successful, proceeding to Communications Agent")
        return "comms"
    else:
        error_msg = state.get('error', 'Unknown museum query error')
        logger.warning(f"Museum query failed: {error_msg}")
        return END


def should_continue_from_comms(state: ChatState) -> str:
    """
    Determine next step after Communications Agent processing
    
    Args:
        state: Current chat state
        
    Returns:
        Next node name or END
    """
    if state.get('success', True) and not state.get('error'):
        logger.info("Communications successful, returning to Manager Agent for final processing")
        return "manager_exit"
    else:
        error_msg = state.get('error', 'Unknown communications error')
        logger.warning(f"Communications failed: {error_msg}")
        return END


def build_museum_chat_graph() -> StateGraph:
    """
    Build the LangGraph workflow for PastPort Museum Chat System
    
    Flow: START -> Manager -> Museum Query -> Comms -> Manager -> END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Building PastPort Museum Chat LangGraph")
    
    # Create the state graph
    workflow = StateGraph(ChatState)
    
    # Add agent nodes - Manager handles both entry and exit
    workflow.add_node("manager_entry", pastport_chat_manager.process_entry)
    workflow.add_node("museum_query", museum_query_agent.process)
    workflow.add_node("comms", comms_agent.process)
    workflow.add_node("manager_exit", pastport_chat_manager.process_exit)
    
    # Define the flow edges
    
    # 1. Start with Manager Agent (Entry)
    workflow.add_edge(START, "manager_entry")
    
    # 2. Conditional flow from Manager Entry
    workflow.add_conditional_edges(
        "manager_entry",
        should_continue_from_manager,
        {
            "museum_query": "museum_query",
            END: END
        }
    )
    
    # 3. Conditional flow from Museum Query Agent
    workflow.add_conditional_edges(
        "museum_query",
        should_continue_from_museum,
        {
            "comms": "comms",
            END: END
        }
    )
    
    # 4. Flow from Communications Agent back to Manager (KEY CHANGE!)
    workflow.add_conditional_edges(
        "comms",
        should_continue_from_comms,
        {
            "manager_exit": "manager_exit",
            END: END
        }
    )
    
    # 5. End after Manager Exit processing
    workflow.add_edge("manager_exit", END)
    
    logger.info("Museum Chat LangGraph built successfully with Manager as central orchestrator")
    return workflow.compile()


def create_initial_state(
    original_query: str,
    session_id: str,
    user_id: str,
    message_id: str,
    user_age_group: str = "adult",
    image_result: Dict[str, Any] = None,
    websocket_callback = None
) -> ChatState:
    """
    Create initial state object for the LangGraph workflow
    
    Args:
        original_query: User's original question
        session_id: Chat session identifier
        user_id: User identifier
        message_id: Unique message identifier
        user_age_group: User's age group for personalization
        image_result: Optional image recognition context
        websocket_callback: Optional callback for sending thinking updates
        
    Returns:
        Initial ChatState object
    """
    return ChatState(
        # Input context
        original_query=original_query,
        session_id=session_id,
        user_id=user_id,
        user_age_group=user_age_group,
        message_id=message_id,
        image_result=image_result,
        
        # Processing context
        chat_history=[],
        processing_stage="initial",
        websocket_callback=websocket_callback,
        
        # Agent results (will be populated during processing)
        manager_validation=None,
        museum_response=None,
        comms_response=None,
        
        # Final output (will be populated during processing)
        final_response="",
        response_source="",
        contexts=[],
        processing_metadata={},
        
        # Error handling
        error=None,
        success=True  # Start optimistically
    )


async def process_museum_chat(
    original_query: str,
    session_id: str,
    user_id: str,
    message_id: str,
    user_age_group: str = "adult",
    image_result: Dict[str, Any] = None,
    websocket_callback = None
) -> Dict[str, Any]:
    """
    Process a museum chat query through the complete agent workflow
    
    Args:
        original_query: User's original question
        session_id: Chat session identifier
        user_id: User identifier
        message_id: Unique message identifier
        user_age_group: User's age group for personalization
        image_result: Optional image recognition context
        websocket_callback: Optional callback for sending thinking updates
        
    Returns:
        Dictionary with final response and metadata
    """
    logger.info(f"Processing museum chat query: '{original_query[:50]}...'")
    
    try:
        # Create the graph
        graph = build_museum_chat_graph()
        
        # Create initial state
        initial_state = create_initial_state(
            original_query=original_query,
            session_id=session_id,
            user_id=user_id,
            message_id=message_id,
            user_age_group=user_age_group,
            image_result=image_result,
            websocket_callback=websocket_callback
        )
        
        # Execute the graph
        logger.info("Executing LangGraph workflow")
        final_state = await graph.ainvoke(initial_state)
        
        # Format final response
        if final_state.get('success', False) and not final_state.get('error'):
            result = {
                "success": True,
                "response": final_state['final_response'],
                "source": final_state['response_source'],
                "contexts": final_state['contexts'],
                "metadata": final_state['processing_metadata'],
                "session_id": session_id,
                "message_id": message_id
            }
            logger.info(f"Museum chat processing completed successfully (source: {final_state['response_source']})")
        else:
            # Handle error case
            error_msg = final_state.get('error', 'Unknown processing error')
            result = {
                "success": False,
                "error": error_msg,
                "response": "I apologize, but I encountered an issue processing your question. Please try asking again or contact museum staff for assistance.",
                "source": "error",
                "contexts": [],
                "metadata": final_state.get('processing_metadata', {}),
                "session_id": session_id,
                "message_id": message_id
            }
            logger.error(f"Museum chat processing failed: {error_msg}")
        
        return result
        
    except Exception as e:
        error_msg = f"LangGraph execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
            "response": "I apologize, but I encountered a technical issue. Please try again or contact museum staff for assistance.",
            "source": "system_error",
            "contexts": [],
            "metadata": {"system_error": True},
            "session_id": session_id,
            "message_id": message_id
        }


# Global graph instance for reuse
_museum_chat_graph = None


def get_museum_chat_graph():
    """
    Get or create the global museum chat graph instance
    
    Returns:
        Compiled StateGraph instance
    """
    global _museum_chat_graph
    if _museum_chat_graph is None:
        _museum_chat_graph = build_museum_chat_graph()
        logger.info("Global museum chat graph initialized")
    return _museum_chat_graph


# Export main functions
__all__ = [
    'build_museum_chat_graph',
    'create_initial_state', 
    'process_museum_chat',
    'get_museum_chat_graph'
]
