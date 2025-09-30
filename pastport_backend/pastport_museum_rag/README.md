# PastPort Museum RAG Package

A museum-focused Retrieval-Augmented Generation system integrated into the PastPort backend. This package provides both CLI and in-process API interfaces for document processing and querying using Ollama models.

## Features

- **Environment-driven configuration** - All settings configurable via environment variables
- **CLI interface** - Complete command-line tool for data management
- **In-process API** - Clean Python API for FastAPI integration
- **Multi-query support** - Intelligent query expansion for better results
- **Idempotent operations** - Safe to re-run data loading without duplicates

## Installation

The package is already integrated into the PastPort backend. Install dependencies:

```bash
conda activate pastport
pip install -r requirements.txt
```

## Prerequisites

1. **Ollama server running:**
   ```bash
   ollama serve
   ```

2. **Required models pulled:**
   ```bash
   ollama pull hf.co/kahhoe/lkc-museum-mistral-v4
   ollama pull mistral:7b-instruct-v0.3-q4_K_M
   ollama pull mxbai-embed-large:335m
   ```

## Configuration

Set environment variables to customize behavior:

```bash
# Database settings
export PASTPORT_CHROMA_DB_PATH="./.chroma/museum"
export PASTPORT_COLLECTION_NAME="lkchm_collection"

# Model settings
export PASTPORT_LLM_MODEL="hf.co/kahhoe/lkc-museum-mistral-v4"
export PASTPORT_MULTIQ_MODEL="mistral:7b-instruct-v0.3-q4_K_M"
export PASTPORT_EMBED_MODEL="mxbai-embed-large:335m"
export OLLAMA_HOST="http://localhost:11434"

# Document processing
export PASTPORT_CHUNK_SIZE="500"
export PASTPORT_CHUNK_OVERLAP="50"
```

## CLI Usage

### Initialize Database
```bash
python -m pastport_museum_rag.cli --mode init
```

### Load Documents
```bash
# Load single species
python -m pastport_museum_rag.cli --mode load --rootfolder="./data" --speciesfolder="rafflesia"

# Load multiple species
python -m pastport_museum_rag.cli --mode load --rootfolder="./data" --speciesfolder="rafflesia,king_cobra"

# Load all species
python -m pastport_museum_rag.cli --mode load --rootfolder="./data" --speciesfolder="all"
```

### Interactive Querying
```bash
python -m pastport_museum_rag.cli --mode query
```

### Check Database Info
```bash
python -m pastport_museum_rag.cli --mode info
```

### Update with New Documents
```bash
python -m pastport_museum_rag.cli --mode update --rootfolder="../PastPort-feature-nlp_kenn_v2/data" --speciesfolder="rafflesia"
```

## Python API Usage

```python
from pastport_museum_rag import VectorDBManager, DocumentProcessor, QueryEngine

# Initialize components
vdb_manager = VectorDBManager()
vdb_manager._initialize()

# Process documents
processor = DocumentProcessor()
doc_count = processor.process_and_add_documents(
    vdb_manager, 
    "../PastPort-feature-nlp_kenn_v2/data", 
    "rafflesia"
)

# Query the system
query_engine = QueryEngine(vdb_manager.vdb)
result = query_engine.query("Tell me about rafflesia")

print(result.answer)
print(f"Found {len(result.contexts)} relevant contexts")
```

## API Reference

### VectorDBManager
- `__init__(db_path, collection_name)` - Initialize with custom paths
- `_initialize()` - Set up the vector database
- `get_collection_info()` - Get database statistics

### DocumentProcessor
- `__init__(chunk_size, chunk_overlap)` - Configure chunking parameters
- `process_and_add_documents(vdb, rootfolder, speciesfolder)` - Process and add documents
- `load_chunks(root_folder, species_folder_names)` - Load and chunk documents

### QueryEngine
- `__init__(vectordb_manager, llm_model, multiq_model)` - Initialize with models
- `query(question, k=5)` - Query and get structured response
- `stream(question, k=5)` - Streaming interface (placeholder)

### QueryResult
- `answer` - The generated answer string
- `contexts` - List of relevant context chunks with metadata
- `to_dict()` - Convert to dictionary format

## Integration with FastAPI

The package can be imported and used within FastAPI routes:

```python
from fastapi import APIRouter
from pastport_museum_rag import VectorDBManager, QueryEngine

router = APIRouter()

# Initialize once at startup
vdb_manager = VectorDBManager()
vdb_manager._initialize()
query_engine = QueryEngine(vdb_manager.vdb)

@router.post("/query")
async def museum_query(question: str):
    result = query_engine.query(question)
    return {
        "answer": result.answer,
        "contexts": result.contexts
    }
```

## File Structure

```
pastport_museum_rag/
├── __init__.py          # Public API exports
├── __main__.py          # Module entry point
├── cli.py               # Command-line interface
├── README.md            # This file
├── config/
│   ├── __init__.py
│   └── settings.py      # Environment-driven configuration
└── core/
    ├── __init__.py
    ├── vectordb.py       # Vector database management
    ├── document_processor.py  # Document processing and chunking
    ├── query_engine.py   # Query processing and LLM integration
    └── update_manager.py # Document update management
```

## Troubleshooting

1. **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
2. **Ollama connection issues**: Check that `ollama serve` is running and models are pulled
3. **Permission errors**: Ensure write permissions for the Chroma database path
4. **Model not found**: Verify model names match exactly what's available in `ollama list`

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PASTPORT_CHROMA_DB_PATH` | `./.chroma/museum` | Vector database storage path |
| `PASTPORT_COLLECTION_NAME` | `lkchm_collection` | Chroma collection name |
| `PASTPORT_LLM_MODEL` | `hf.co/kahhoe/lkc-museum-mistral-v4` | Main LLM model |
| `PASTPORT_MULTIQ_MODEL` | `mistral:7b-instruct-v0.3-q4_K_M` | Multi-query analysis model |
| `PASTPORT_EMBED_MODEL` | `mxbai-embed-large:335m` | Embedding model |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `PASTPORT_CHUNK_SIZE` | `500` | Document chunk size |
| `PASTPORT_CHUNK_OVERLAP` | `50` | Chunk overlap size |
