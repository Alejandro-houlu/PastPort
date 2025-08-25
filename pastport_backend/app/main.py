from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.mainCam_recognition import router as mainCam_router
from app.api.artifacts_api import router as artifacts_router
from app.websocket.mainCam_handler import handle_mainCam_websocket_connection

# Create FastAPI app
app = FastAPI(
    title="PastPort Data Processor",
    description="FastAPI backend for PastPort data processing application",
    version="1.0.0",
    debug=settings.debug
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


@app.websocket("/ws/mainCam")
async def websocket_mainCam_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time mainCam recognition"""
    await handle_mainCam_websocket_connection(websocket)

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
