# PastPort Museum RAG Integration - Part 2 Implementation

## Overview

This document describes the Part 2 implementation of the PastPort Museum RAG Integration, which focuses on FastAPI integration with WebSocket functionality for real-time chat communication.

## Architecture

```
Frontend WebSocket ↔ FastAPI Backend ↔ LangGraph Agent ↔ Museum RAG System ↔ Ollama LLM
```

## Implementation Summary

### ✅ Completed Components

#### 1. RAG Dependency Injection System (`app/dependencies/rag.py`)
- **Singleton Pattern**: Global instances of VectorDBManager, DocumentProcessor, and QueryEngine
- **Fail-Fast Initialization**: RAG system initializes at FastAPI startup with comprehensive error handling
- **Health Monitoring**: Status checking functions for system health endpoints
- **Clean Dependency Injection**: FastAPI dependencies for WebSocket handlers and API endpoints

**Key Features:**
- Environment-driven configuration using RAG settings
- Automatic warmup query for early failure detection
- Comprehensive logging of initialization process
- Graceful degradation if RAG system fails to initialize

#### 2. FastAPI Startup Integration (`app/main.py`)
- **Lifespan Management**: Uses FastAPI lifespan context manager for startup/shutdown
- **RAG Initialization**: Automatic RAG system initialization at application startup
- **Error Handling**: Continues operation even if RAG system fails to initialize
- **Logging**: Comprehensive startup and shutdown logging

**Integration Points:**
- RAG components initialized before serving requests
- Clean shutdown with resource cleanup
- WebSocket endpoint registration for museum chat

#### 3. Health Endpoints (`app/api/health.py`)
- **`GET /api/v1/health/ollama`**: Check Ollama server availability and model status
- **`GET /api/v1/health/rag`**: Check RAG system status and vector database health

**Health Check Features:**
- Ollama server connectivity testing
- Required model availability verification
- Vector database collection status
- RAG system component status
- Test query execution for end-to-end validation

#### 4. WebSocket Chat Endpoint (`app/websocket/museum_chat_handler.py`)
- **`WS /ws/chat`**: Real-time chat interface for frontend communication
- **Connection Management**: Multi-client connection handling with unique client IDs
- **Message Protocol**: Structured JSON message format for different message types
- **Error Handling**: Comprehensive error handling with user-friendly messages

**Supported Message Types:**
- `query`: Museum-related questions processed through the agent
- `ping`: Connection health check (responds with `pong`)
- `status`: System status request
- Error handling for invalid JSON and unknown message types

#### 5. LangGraph Agent Framework (`app/agents/museum_agent.py`)
- **Agent Workflow**: Multi-node processing pipeline for query handling
- **State Management**: Comprehensive context tracking through agent nodes
- **Error Recovery**: Graceful error handling with user-friendly responses
- **Extensible Design**: Easy to extend with additional processing nodes

**Agent Workflow:**
1. **Analyze Query Node**: Query analysis and preprocessing
2. **Query RAG Node**: RAG system interaction with status checking
3. **Format Response Node**: Response formatting for frontend consumption

#### 6. End-to-End Testing (`test_websocket_chat.py`)
- **Automated Tests**: Comprehensive WebSocket functionality testing
- **Interactive Mode**: Manual testing interface for development
- **Test Coverage**: Ping/pong, status requests, queries, and error handling

## API Endpoints

### Health Endpoints
```
GET /api/v1/health/ollama    - Check Ollama server and models
GET /api/v1/health/rag       - Check RAG system status
```

### WebSocket Endpoints
```
WS /ws/chat                  - Museum chat interface
```

## WebSocket Message Protocol

### Client → Server Messages

#### Query Message
```json
{
  "type": "query",
  "message": "Tell me about rafflesia",
  "session_id": "optional_session_id",
  "max_results": 5
}
```

#### Ping Message
```json
{
  "type": "ping",
  "message": "ping",
  "session_id": "optional_session_id"
}
```

#### Status Message
```json
{
  "type": "status",
  "message": "get status",
  "session_id": "optional_session_id"
}
```

### Server → Client Responses

#### Query Response
```json
{
  "type": "response",
  "message": "Rafflesia is the world's largest flower...",
  "sources": [
    {
      "content": "Document excerpt...",
      "metadata": {"source": "file.pdf", "page": 1}
    }
  ],
  "session_id": "optional_session_id",
  "metadata": {
    "original_query": "Tell me about rafflesia",
    "sources_count": 3,
    "agent_state": "complete"
  }
}
```

#### Error Response
```json
{
  "type": "error",
  "message": "User-friendly error message",
  "session_id": "optional_session_id",
  "metadata": {
    "error_occurred": true,
    "agent_state": "error"
  }
}
```

## Testing

### Automated Testing
```bash
cd pastport_backend
python test_websocket_chat.py
```

### Interactive Testing
```bash
cd pastport_backend
python test_websocket_chat.py interactive
```

### Health Check Testing
```bash
# Check Ollama status
curl http://localhost:8000/api/v1/health/ollama

# Check RAG system status
curl http://localhost:8000/api/v1/health/rag
```

## Configuration

The system uses the existing RAG configuration from Part 1:

```bash
# Environment variables
PASTPORT_LLM_MODEL="hf.co/kahhoe/lkc-museum-mistral-v4"
PASTPORT_MULTIQ_MODEL="mistral:7b-instruct-v0.3-q4_K_M"
PASTPORT_EMBED_MODEL="mxbai-embed-large:335m"
```

## Dependencies Added

```
httpx          # For Ollama health checks
websockets     # For WebSocket testing
```

## File Structure

```
pastport_backend/
├── app/
│   ├── dependencies/
│   │   └── rag.py                    # RAG dependency injection
│   ├── api/
│   │   └── health.py                 # Health endpoints (updated)
│   ├── websocket/
│   │   └── museum_chat_handler.py    # WebSocket chat handler
│   ├── agents/
│   │   ├── __init__.py
│   │   └── museum_agent.py           # LangGraph agent framework
│   └── main.py                       # FastAPI app (updated)
├── test_websocket_chat.py            # WebSocket testing script
├── requirements.txt                  # Updated dependencies
└── MUSEUM_RAG_INTEGRATION.md         # This documentation
```

## Usage Examples

### Frontend WebSocket Connection (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = function(event) {
    console.log('Connected to museum chat');
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    console.log('Received:', response);
};

// Send a query
ws.send(JSON.stringify({
    type: 'query',
    message: 'Tell me about the sperm whale',
    session_id: 'user_session_123'
}));
```

### Python Client Example
```python
import asyncio
import websockets
import json

async def chat_with_museum():
    uri = "ws://localhost:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        # Send query
        await websocket.send(json.dumps({
            "type": "query",
            "message": "What can you tell me about dinosaurs?",
            "session_id": "python_client"
        }))
        
        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Bot: {data['message']}")

asyncio.run(chat_with_museum())
```

## Next Steps for Frontend Integration

1. **WebSocket Connection**: Connect to `ws://localhost:8000/ws/chat`
2. **Message Handling**: Implement JSON message protocol
3. **UI Components**: Create chat interface with message display
4. **Source Display**: Show retrieved document sources to users
5. **Error Handling**: Handle connection errors and system unavailability
6. **Session Management**: Implement session IDs for conversation tracking

## Troubleshooting

### Common Issues

1. **RAG System Not Ready**
   - Check Ollama server is running: `ollama list`
   - Verify models are pulled: `ollama pull mistral:7b-instruct-v0.3-q4_K_M`
   - Check vector database exists: Look for `.chroma/museum/` directory

2. **WebSocket Connection Failed**
   - Ensure FastAPI server is running on port 8000
   - Check CORS settings allow WebSocket connections
   - Verify no firewall blocking WebSocket connections

3. **Health Checks Failing**
   - Ollama health: Ensure Ollama server is accessible on localhost:11434
   - RAG health: Check RAG system initialization logs during startup

### Debugging

Enable debug logging by setting environment variable:
```bash
export DEBUG=true
```

Check application logs for detailed error information during startup and operation.

## Performance Considerations

- **Connection Pooling**: WebSocket connections are managed efficiently
- **Memory Usage**: RAG components are singletons to minimize memory footprint
- **Response Time**: Agent framework adds minimal overhead to query processing
- **Concurrent Users**: System supports multiple simultaneous WebSocket connections

## Security Considerations

- **Input Validation**: All WebSocket messages are validated using Pydantic models
- **Error Handling**: Sensitive error information is not exposed to clients
- **Connection Management**: Proper cleanup of disconnected clients
- **Rate Limiting**: Consider implementing rate limiting for production use

---

This completes the Part 2 implementation of the PastPort Museum RAG Integration. The system is now ready for frontend integration and provides a robust foundation for real-time museum chat functionality.
