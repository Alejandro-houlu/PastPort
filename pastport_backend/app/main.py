import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.mainCam_recognition import router as mainCam_router
from app.api.artifacts_api import router as artifacts_router
from app.api.user_click_history_api import router as user_clicks_router
from app.api.chat_history_api import router as chat_history_router
from app.api.question_recommender_api import router as question_recommender_router
from app.websocket.mainCam_handler import handle_mainCam_websocket_connection
from app.websocket.museum_chat_handler import handle_museum_chat_websocket_connection
from app.dependencies.rag import initialize_rag_system, cleanup_rag_system, RAGInitializationError
from app.dependencies.question_recommender import (
    initialize_question_recommender, 
    cleanup_question_recommender, 
    QuestionRecommenderInitializationError
)

# Configure logging
logging.basicConfig(
    filename='app.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting PastPort Data Processor...")
    
    try:
        # Initialize RAG system
        logger.info("Initializing Museum RAG system...")
        initialize_rag_system()
        logger.info("Museum RAG system initialized successfully!")
    except RAGInitializationError as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        logger.warning("Application will continue without RAG functionality")
    except Exception as e:
        logger.error(f"Unexpected error during RAG initialization: {e}", exc_info=True)
        logger.warning("Application will continue without RAG functionality")
    
    try:
        # Initialize Question Recommender system
        logger.info("Initializing Question Recommender system...")
        initialize_question_recommender()
        logger.info("Question Recommender system initialized successfully!")
    except QuestionRecommenderInitializationError as e:
        logger.error(f"Failed to initialize Question Recommender system: {e}")
        logger.warning("Application will continue without Question Recommender functionality")
    except Exception as e:
        logger.error(f"Unexpected error during Question Recommender initialization: {e}", exc_info=True)
        logger.warning("Application will continue without Question Recommender functionality")
    
    logger.info("PastPort Data Processor startup completed!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PastPort Data Processor...")
    cleanup_rag_system()
    cleanup_question_recommender()
    logger.info("PastPort Data Processor shutdown completed!")

# Create FastAPI app
app = FastAPI(
    title="PastPort Data Processor",
    description="FastAPI backend for PastPort data processing application",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(auth_router, tags=["authentication"])
app.include_router(mainCam_router, prefix="/api/v1/mainCam", tags=["mainCam recognition"])
app.include_router(artifacts_router, prefix="/api/v1", tags=["artifacts"])
app.include_router(user_clicks_router, tags=["user_click_history"])
app.include_router(chat_history_router, tags=["chat_history"])
app.include_router(question_recommender_router)


@app.websocket("/ws/mainCam")
async def websocket_mainCam_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time mainCam recognition"""
    await handle_mainCam_websocket_connection(websocket)


@app.websocket("/ws/chat")
async def websocket_museum_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time museum chat with RAG system"""
    await handle_museum_chat_websocket_connection(websocket)

@app.get("/")
async def root():
    return {
        "message": "Welcome to PastPort Data Processor API",
        "version": "1.0.0",
        "environment": settings.environment
    }

@app.get("/favicon.ico")
async def favicon():
    """Return a simple favicon to prevent 404 errors"""
    # Simple 1x1 transparent PNG favicon
    favicon_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=favicon_data, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
