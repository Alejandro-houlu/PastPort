from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.dependencies.authentication import get_current_active_user
from app.models.user import User

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
