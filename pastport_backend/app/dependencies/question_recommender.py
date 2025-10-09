"""
FastAPI Question Recommender dependencies
Handles Question Recommender system initialization and dependency injection
"""
import logging
from typing import Optional
from pathlib import Path
from fastapi import HTTPException, status
from functools import lru_cache

from app.services.question_recommender_service import QuestionRecommenderService

logger = logging.getLogger(__name__)

# Global singleton instance
_recommender_service: Optional[QuestionRecommenderService] = None
_initialization_error: Optional[str] = None


class QuestionRecommenderInitializationError(Exception):
    """Raised when Question Recommender system fails to initialize"""
    pass


def initialize_question_recommender() -> None:
    """
    Initialize the Question Recommender system at application startup.
    This should be called once during FastAPI startup.
    
    Raises:
        QuestionRecommenderInitializationError: If initialization fails
    """
    global _recommender_service, _initialization_error
    
    try:
        logger.info("Initializing Question Recommender system...")
        
        # Set paths for model and data
        model_dir = Path(__file__).parent.parent / "ml_models" / "question_recommender" / "bert-qclass-model_3"
        data_file = Path(__file__).parent.parent / "ml_models" / "question_recommender" / "QA_pairs.json"
        
        logger.info(f"Model directory: {model_dir}")
        logger.info(f"Data file: {data_file}")
        
        # Check if paths exist
        if not model_dir.exists():
            raise QuestionRecommenderInitializationError(f"Model directory not found: {model_dir}")
        if not data_file.exists():
            raise QuestionRecommenderInitializationError(f"Data file not found: {data_file}")
        
        # Initialize the service
        _recommender_service = QuestionRecommenderService(
            model_dir=str(model_dir),
            data_file=str(data_file)
        )
        
        logger.info("Question Recommender system initialized successfully!")
        _initialization_error = None
        
    except Exception as e:
        error_msg = f"Failed to initialize Question Recommender system: {str(e)}"
        logger.error(error_msg, exc_info=True)
        _initialization_error = error_msg
        
        # Reset service on failure
        _recommender_service = None
        
        raise QuestionRecommenderInitializationError(error_msg) from e


def get_recommender_status() -> dict:
    """
    Get the current status of the Question Recommender system.
    
    Returns:
        Dictionary with system status information
    """
    global _recommender_service, _initialization_error
    
    if _initialization_error:
        return {
            "status": "error",
            "error": _initialization_error,
            "initialized": False
        }
    
    is_initialized = _recommender_service is not None
    
    return {
        "status": "ready" if is_initialized else "not_initialized",
        "initialized": is_initialized
    }


@lru_cache()
def get_question_recommender() -> QuestionRecommenderService:
    """
    Get the singleton QuestionRecommenderService instance.
    
    Returns:
        QuestionRecommenderService instance
    
    Raises:
        HTTPException: If system is not initialized
    """
    global _recommender_service, _initialization_error
    
    if _initialization_error:
        # Log error but don't raise exception (silent failure as per requirements)
        logger.error(f"Question Recommender not available: {_initialization_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Question Recommender service unavailable"
        )
    
    if _recommender_service is None:
        logger.error("Question Recommender system not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Question Recommender service unavailable"
        )
    
    return _recommender_service


def cleanup_question_recommender() -> None:
    """
    Clean up Question Recommender system resources.
    This should be called during application shutdown.
    """
    global _recommender_service, _initialization_error
    
    logger.info("Cleaning up Question Recommender system...")
    
    # Reset global variables
    _recommender_service = None
    _initialization_error = None
    
    # Clear LRU cache
    get_question_recommender.cache_clear()
    
    logger.info("Question Recommender system cleanup completed")
