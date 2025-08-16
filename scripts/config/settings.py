import os
from pathlib import Path

class Config:
    # Database settings
    CHROMA_DB_PATH = "../chroma_langchain_db"
    COLLECTION_NAME = "lkchm_collection"
    
    # Document processing
    DEFAULT_ROOT_FOLDER = "../data"
    DEFAULT_SPECIES_FOLDER = "dinosaur_sauropod"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 100
    
    # Embedding settings
    EMBEDDING_MODEL = "nomic-embed-text"
    
    # LLM settings
    LLM_MODEL = "deepseek-r1:8b"
    
    # File types to process
    SUPPORTED_EXTENSIONS = [".pdf", ".md", ".txt"]