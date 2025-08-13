from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db

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
