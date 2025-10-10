import os
from pathlib import Path

class Config:
    # Database settings
    CHROMA_DB_PATH = os.getenv("PASTPORT_CHROMA_DB_PATH", "./.chroma/museum")
    COLLECTION_NAME = os.getenv("PASTPORT_COLLECTION_NAME", "lkchm_collection")
    
    # Document processing
    DEFAULT_ROOT_FOLDER = os.getenv("PASTPORT_DEFAULT_ROOT_FOLDER", "./data")
    DEFAULT_SPECIES_FOLDER = os.getenv("PASTPORT_DEFAULT_SPECIES_FOLDER", "dinosaur_sauropod")
    CHUNK_SIZE = int(os.getenv("PASTPORT_CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("PASTPORT_CHUNK_OVERLAP", "100"))

    # MULTIQUERY MODEL
    MULTIQ_MODEL = os.getenv("PASTPORT_MULTIQ_MODEL", "hf.co/kahhoe/lkc-museum-mistral-v4")
    #mistral:7b-instruct-v0.3-q4_K_M
    
    # Embedding settings
    EMBEDDING_MODEL = os.getenv("PASTPORT_EMBED_MODEL", "mxbai-embed-large:335m")
    
    # LLM settings
    LLM_MODEL = os.getenv("PASTPORT_LLM_MODEL", "hf.co/kahhoe/lkc-museum-mistral-v4")
    
    # Ollama settings
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # File types to process
    SUPPORTED_EXTENSIONS = [".pdf", ".md", ".txt"]
