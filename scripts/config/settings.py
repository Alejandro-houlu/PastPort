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

    # MULTIQUERY MODEL
    MULTIQ_MODEL = "unsloth-mistral-7b-instruct-v0.3-bnb-4bit-q4_k_m"
    
    # Embedding settings
    EMBEDDING_MODEL = "mxbai-embed-large:335m"
    # OR "nomic-embed-text"
    
    # LLM settings
    LLM_MODEL = "unsloth-mistral-7b-instruct-v0.3-bnb-4bit-q4_k_m"
    # OR llama3.1:8b
    # OR mistral:7b
    # OR mistral:7b-instruct-v0.3-q4_K_M
    # OR deepseek-r1:8b
    # OR unsloth-mistral-7b-instruct-v0.3-bnb-4bit-q4_k_m
    
    # File types to process
    SUPPORTED_EXTENSIONS = [".pdf", ".md", ".txt"]