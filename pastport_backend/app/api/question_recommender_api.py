"""
Question Recommender API for PastPort
Handles question recommendation requests based on artifact and user questions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List
import logging

from app.dependencies.authentication import get_current_user
from app.dependencies.question_recommender import get_question_recommender
from app.models.user import User
from app.services.question_recommender_service import QuestionRecommenderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/question-recommender", tags=["question_recommender"])


class QuestionRecommendationRequest(BaseModel):
    """Request model for question recommendations"""
    artifact_name: str = Field(..., description="Name of the artifact/species")
    question: str = Field(None, description="User's question (optional, defaults to generic question)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "artifact_name": "Sauropods"
            }
        }


class QuestionRecommendationResponse(BaseModel):
    """Response model for question recommendations"""
    success: bool
    artifact_name: str
    questions: Dict[str, List[str]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "artifact_name": "Sauropods",
                "questions": {
                    "same_intent_species": ["What did sauropods eat?"],
                    "diff_intent_same_species": ["How tall were sauropods?"],
                    "diff_species_same_intent": ["What did T-Rex eat?"],
                    "diff_species_intent": ["How fast could velociraptors run?"]
                }
            }
        }


def format_artifact_name(artifact_name: str) -> str:
    """
    Format artifact name from database format to model format.
    Database: sperm_whale, rafflesia_arnoldii
    Model: Sperm Whale, Rafflesia Arnoldii
    
    Args:
        artifact_name: Name in database format (lowercase with underscores)
        
    Returns:
        Name formatted for the model (Title Case with spaces)
    """
    # Split by underscore and capitalize first letter of each word
    words = artifact_name.split('_')
    formatted_name = ' '.join(word.capitalize() for word in words)
    return formatted_name


@router.post("/suggestions", response_model=QuestionRecommendationResponse)
async def get_question_recommendations(
    request: QuestionRecommendationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get question recommendations based on artifact name and optional user question.
    
    If no question is provided, a default question will be generated:
    "Tell me more about {artifact_name}"
    
    Returns 4 questions (one from each category):
    - same_intent_species: Same intent and same species
    - diff_intent_same_species: Different intent but same species
    - diff_species_same_intent: Same intent but different species
    - diff_species_intent: Different intent and different species
    
    Args:
        request: Question recommendation request with artifact name and optional question
        current_user: Authenticated user (JWT required)
    
    Returns:
        JSON with 4 recommended questions
    
    Raises:
        HTTPException: If recommender service is unavailable or error occurs
    """
    try:
        # Format artifact name for the model (e.g., sperm_whale -> Sperm Whale)
        formatted_artifact_name = format_artifact_name(request.artifact_name)
        logger.info(f"Question recommendation request for artifact: {request.artifact_name} (formatted: {formatted_artifact_name})")
        
        # Get recommender service (will raise HTTPException if not available)
        try:
            recommender_service: QuestionRecommenderService = get_question_recommender()
        except HTTPException:
            # Silent failure - return empty recommendations
            logger.warning(f"Question recommender service unavailable for {request.artifact_name}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": False,
                    "artifact_name": request.artifact_name,
                    "questions": {
                        "same_intent_species": [],
                        "diff_intent_same_species": [],
                        "diff_species_same_intent": [],
                        "diff_species_intent": []
                    }
                }
            )
        
        # Generate default question if not provided (use formatted name for display)
        question = request.question
        if not question:
            question = f"Tell me more about {formatted_artifact_name}"
            logger.info(f"Using default question: {question}")
        
        # Get recommendations using formatted artifact name
        recommendations = recommender_service.get_recommendations(
            species=formatted_artifact_name,
            question=question
        )
        
        # Handle None response (error during recommendation)
        if recommendations is None:
            logger.warning(f"Failed to generate recommendations for {request.artifact_name}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": False,
                    "artifact_name": request.artifact_name,
                    "questions": {
                        "same_intent_species": [],
                        "diff_intent_same_species": [],
                        "diff_species_same_intent": [],
                        "diff_species_intent": []
                    }
                }
            )
        
        logger.info(f"Successfully generated recommendations for {request.artifact_name}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "artifact_name": request.artifact_name,
                "questions": recommendations
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log error but don't raise - silent failure
        logger.error(f"Unexpected error getting question recommendations: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": False,
                "artifact_name": request.artifact_name,
                "questions": {
                    "same_intent_species": [],
                    "diff_intent_same_species": [],
                    "diff_species_same_intent": [],
                    "diff_species_intent": []
                }
            }
        )


@router.get("/status")
async def get_recommender_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of the question recommender service.
    
    Args:
        current_user: Authenticated user (JWT required)
    
    Returns:
        JSON with service status information
    """
    from app.dependencies.question_recommender import get_recommender_status
    
    status_info = get_recommender_status()
    return JSONResponse(content=status_info)
