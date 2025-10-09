"""
FastAPI RAG dependencies
Handles Museum RAG system initialization and dependency injection
"""
import logging
from typing import Optional
from fastapi import HTTPException, status
from functools import lru_cache

from pastport_museum_rag import VectorDBManager, DocumentProcessor, QueryEngine
from pastport_museum_rag.config.settings import Config as RAGConfig

logger = logging.getLogger(__name__)

# Global singleton instances
_vector_db_manager: Optional[VectorDBManager] = None
_document_processor: Optional[DocumentProcessor] = None
_query_engine: Optional[QueryEngine] = None
_initialization_error: Optional[str] = None


class RAGInitializationError(Exception):
    """Raised when RAG system fails to initialize"""
    pass


def initialize_rag_system() -> None:
    """
    Initialize the RAG system components at application startup.
    This should be called once during FastAPI startup.
    
    Raises:
        RAGInitializationError: If initialization fails
    """
    global _vector_db_manager, _document_processor, _query_engine, _initialization_error
    
    try:
        logger.info("Initializing Museum RAG system...")
        
        # Get RAG settings
        rag_config = RAGConfig()
        logger.info(f"RAG Configuration:")
        logger.info(f"  LLM Model: {rag_config.LLM_MODEL}")
        logger.info(f"  MultiQ Model: {rag_config.MULTIQ_MODEL}")
        logger.info(f"  Embed Model: {rag_config.EMBEDDING_MODEL}")
        logger.info(f"  Vector DB Path: {rag_config.CHROMA_DB_PATH}")
        
        # Initialize VectorDBManager
        logger.info("Initializing VectorDBManager...")
        _vector_db_manager = VectorDBManager()
        _vector_db_manager._initialize()
        
        # Get collection info for logging
        try:
            collection_info = _vector_db_manager.get_collection_info()
            if collection_info:
                logger.info(f"Vector DB Collection: {collection_info['name']} with {collection_info['id_counts']} documents")
            else:
                logger.warning("No collection information available")
        except Exception as e:
            logger.warning(f"Could not retrieve collection info: {e}")
        
        # Initialize DocumentProcessor
        logger.info("Initializing DocumentProcessor...")
        _document_processor = DocumentProcessor()
        
        # Initialize QueryEngine
        logger.info("Initializing QueryEngine...")
        _query_engine = QueryEngine(_vector_db_manager.vdb)
        
        # Optional: Perform warmup query to test the system
        # logger.info("Performing warmup query...")
        # try:
        #     warmup_result = _query_engine.query("What is this museum about?", k=1)
        #     logger.info(warmup_result.answer)
        #     logger.info(f"Warmup query successful. Response length: {len(warmup_result.answer)} chars")
        # except Exception as e:
        #     logger.warning(f"Warmup query failed (non-critical): {e}")
        
        logger.info("Museum RAG system initialized successfully!")
        _initialization_error = None
        
    except Exception as e:
        error_msg = f"Failed to initialize RAG system: {str(e)}"
        logger.error(error_msg, exc_info=True)
        _initialization_error = error_msg
        
        # Reset all components on failure
        _vector_db_manager = None
        _document_processor = None
        _query_engine = None
        
        raise RAGInitializationError(error_msg) from e


def get_rag_status() -> dict:
    """
    Get the current status of the RAG system.
    
    Returns:
        Dictionary with RAG system status information
    """
    global _vector_db_manager, _document_processor, _query_engine, _initialization_error
    
    if _initialization_error:
        return {
            "status": "error",
            "error": _initialization_error,
            "components": {
                "vector_db_manager": False,
                "document_processor": False,
                "query_engine": False
            }
        }
    
    components_status = {
        "vector_db_manager": _vector_db_manager is not None,
        "document_processor": _document_processor is not None,
        "query_engine": _query_engine is not None
    }
    
    all_initialized = all(components_status.values())
    
    status_info = {
        "status": "ready" if all_initialized else "partial",
        "components": components_status
    }
    
    # Add collection info if vector DB is available
    if _vector_db_manager and _vector_db_manager.vdb:
        try:
            collection_info = _vector_db_manager.get_collection_info()
            if collection_info:
                status_info["collections"] = {
                    collection_info["name"]: collection_info["id_counts"]
                }
            else:
                status_info["collections"] = {}
        except Exception as e:
            status_info["collections_error"] = str(e)
    
    return status_info


@lru_cache()
def get_vector_db_manager() -> VectorDBManager:
    """
    Get the singleton VectorDBManager instance.
    
    Returns:
        VectorDBManager instance
    
    Raises:
        HTTPException: If RAG system is not initialized
    """
    global _vector_db_manager, _initialization_error
    
    if _initialization_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG system initialization failed: {_initialization_error}"
        )
    
    if _vector_db_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not initialized. VectorDBManager unavailable."
        )
    
    return _vector_db_manager


@lru_cache()
def get_document_processor() -> DocumentProcessor:
    """
    Get the singleton DocumentProcessor instance.
    
    Returns:
        DocumentProcessor instance
    
    Raises:
        HTTPException: If RAG system is not initialized
    """
    global _document_processor, _initialization_error
    
    if _initialization_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG system initialization failed: {_initialization_error}"
        )
    
    if _document_processor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not initialized. DocumentProcessor unavailable."
        )
    
    return _document_processor


@lru_cache()
def get_query_engine() -> QueryEngine:
    """
    Get the singleton QueryEngine instance.
    
    Returns:
        QueryEngine instance
    
    Raises:
        HTTPException: If RAG system is not initialized
    """
    global _query_engine, _initialization_error
    
    if _initialization_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG system initialization failed: {_initialization_error}"
        )
    
    if _query_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not initialized. QueryEngine unavailable."
        )
    
    return _query_engine


def cleanup_rag_system() -> None:
    """
    Clean up RAG system resources.
    This should be called during application shutdown.
    """
    global _vector_db_manager, _document_processor, _query_engine, _initialization_error
    
    logger.info("Cleaning up RAG system...")
    
    # Reset all global variables
    _vector_db_manager = None
    _document_processor = None
    _query_engine = None
    _initialization_error = None
    
    # Clear LRU cache
    get_vector_db_manager.cache_clear()
    get_document_processor.cache_clear()
    get_query_engine.cache_clear()
    
    logger.info("RAG system cleanup completed")
