"""
PastPort Museum RAG Package

A museum-focused Retrieval-Augmented Generation system for the PastPort application.
Provides both CLI and in-process API interfaces for document processing and querying.

Public API:
- VectorDBManager: Manages vector database operations
- DocumentProcessor: Processes and chunks documents
- QueryEngine: Handles queries and generates responses
- QueryResult: Structured query response object

Usage:
    # Initialize components
    from pastport_museum_rag import VectorDBManager, DocumentProcessor, QueryEngine
    
    # Set up vector database
    vdb_manager = VectorDBManager()
    vdb_manager._initialize()
    
    # Process documents
    processor = DocumentProcessor()
    doc_count = processor.process_and_add_documents(vdb_manager, "data", "rafflesia")
    
    # Query the system
    query_engine = QueryEngine(vdb_manager.vdb)
    result = query_engine.query("Tell me about rafflesia")
    print(result.answer)
"""

from .core.vectordb import VectorDBManager
from .core.document_processor import DocumentProcessor
from .core.query_engine import QueryEngine, QueryResult

__version__ = "1.0.0"
__all__ = ["VectorDBManager", "DocumentProcessor", "QueryEngine", "QueryResult"]
