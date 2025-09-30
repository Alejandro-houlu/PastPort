import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.dependencies.authentication import get_current_active_user
from app.dependencies.rag import get_rag_status, get_query_engine
from app.models.user import User
from pastport_museum_rag.config.settings import Config as RAGConfig

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "message": "PastPort Data Processor is running"
    }

@router.get("/health/db")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Database connectivity health check"""
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        await db.commit()
        
        return {
            "status": "healthy",
            "message": "Database connection is working",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Database connection failed",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/health/auth")
async def jwt_auth_test(current_user: User = Depends(get_current_active_user)):
    """
    JWT Authentication Test Endpoint
    
    This endpoint requires a valid JWT token in the Authorization header.
    Use this to test if your JWT token from login works properly.
    
    Headers required:
    Authorization: Bearer <your_jwt_token>
    
    Returns:
        User information if JWT token is valid
    
    Raises:
        401: If token is missing, invalid, or expired
        403: If user is inactive
    """
    return {
        "status": "success",
        "message": "JWT authentication successful! 🎉",
        "authenticated_user": {
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "auth_method": current_user.auth_method,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        },
        "token_info": {
            "description": "Your JWT token is valid and working correctly",
            "next_steps": "You can now use this token for all protected endpoints"
        }
    }


@router.get("/health/ollama")
async def ollama_health_check():
    """
    Check Ollama server availability and model status
    """
    try:
        rag_config = RAGConfig()
        
        # Check if Ollama server is running
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    models_data = response.json()
                    available_models = [model["name"] for model in models_data.get("models", [])]
                    
                    # Check if required models are available
                    required_models = [
                        rag_config.LLM_MODEL,
                        rag_config.MULTIQ_MODEL,
                        rag_config.EMBEDDING_MODEL
                    ]
                    
                    missing_models = []
                    for model in required_models:
                        if not any(model in available_model for available_model in available_models):
                            missing_models.append(model)
                    
                    if missing_models:
                        return {
                            "status": "partial",
                            "message": "Ollama server is running but some required models are missing",
                            "ollama_server": "connected",
                            "available_models": available_models,
                            "required_models": required_models,
                            "missing_models": missing_models,
                            "warning": "Some RAG functionality may not work properly"
                        }
                    else:
                        return {
                            "status": "healthy",
                            "message": "Ollama server is running and all required models are available",
                            "ollama_server": "connected",
                            "available_models": available_models,
                            "required_models": required_models,
                            "missing_models": []
                        }
                else:
                    return {
                        "status": "unhealthy",
                        "message": "Ollama server responded with error",
                        "ollama_server": "error",
                        "error": f"HTTP {response.status_code}"
                    }
            except httpx.ConnectError:
                return {
                    "status": "unhealthy",
                    "message": "Cannot connect to Ollama server",
                    "ollama_server": "disconnected",
                    "error": "Connection refused - is Ollama running on localhost:11434?"
                }
            except httpx.TimeoutException:
                return {
                    "status": "unhealthy",
                    "message": "Ollama server connection timeout",
                    "ollama_server": "timeout",
                    "error": "Request timed out after 10 seconds"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Error checking Ollama server",
            "ollama_server": "error",
            "error": str(e)
        }


@router.get("/health/rag")
async def rag_health_check():
    """
    Check RAG system status and vector database health
    """
    try:
        rag_status = get_rag_status()
        rag_config = RAGConfig()
        
        # Add configuration info
        rag_status["configuration"] = {
            "llm_model": rag_config.LLM_MODEL,
            "multiq_model": rag_config.MULTIQ_MODEL,
            "embed_model": rag_config.EMBEDDING_MODEL,
            "vector_db_path": str(rag_config.CHROMA_DB_PATH)
        }
        
        # Test query engine if available
        if rag_status["status"] == "ready":
            try:
                query_engine = get_query_engine()
                test_result = query_engine.query("test", max_results=1)
                rag_status["query_test"] = {
                    "status": "success",
                    "response_length": len(test_result.response),
                    "sources_count": len(test_result.sources)
                }
            except Exception as e:
                rag_status["query_test"] = {
                    "status": "failed",
                    "error": str(e)
                }
                rag_status["status"] = "partial"
                rag_status["message"] = "RAG components initialized but query test failed"
        
        return rag_status
        
    except Exception as e:
        return {
            "status": "error",
            "message": "Error checking RAG system",
            "error": str(e)
        }
