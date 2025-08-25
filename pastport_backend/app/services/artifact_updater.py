"""
Artifact Updater Service for PastPort
Automatically populates artifacts database with YOLO model labels
"""
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ultralytics import YOLO

from ..models.artifact import Artifact
from ..database import AsyncSessionLocal


class ArtifactUpdaterService:
    """Service to update artifacts database with YOLO model labels"""
    
    def __init__(self, model_path: str):
        """
        Initialize the artifact updater service
        
        Args:
            model_path: Path to the YOLO model file
        """
        self.model_path = Path(model_path)
        self.model: Optional[YOLO] = None
        
    def load_model(self) -> None:
        """Load the YOLO model"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"YOLO model not found at: {self.model_path}")
        
        print(f"Loading YOLO model from: {self.model_path}")
        self.model = YOLO(str(self.model_path))
        print(f"Model loaded successfully. Found {len(self.model.names)} labels.")
    
    def get_model_labels(self) -> List[str]:
        """
        Extract all label names from the YOLO model
        
        Returns:
            List of artifact names from the model
        """
        if self.model is None:
            self.load_model()
        
        # Get labels from model.names (dict with id: name mapping)
        labels = list(self.model.names.values())
        print(f"Extracted labels: {labels}")
        return labels
    
    async def get_existing_artifacts(self, session: AsyncSession) -> List[str]:
        """
        Get list of existing artifact names from database
        
        Args:
            session: Database session
            
        Returns:
            List of existing artifact names
        """
        result = await session.execute(
            select(Artifact.artifact_name)
        )
        existing_names = [row[0] for row in result.fetchall()]
        print(f"Found {len(existing_names)} existing artifacts in database")
        return existing_names
    
    async def create_artifact(self, session: AsyncSession, artifact_name: str) -> Artifact:
        """
        Create a new artifact in the database
        
        Args:
            session: Database session
            artifact_name: Name of the artifact
            
        Returns:
            Created Artifact instance
        """
        # Generate 8-character UUID
        artifact_id = str(uuid.uuid4())[:8]
        
        # Create new artifact with default values
        artifact = Artifact(
            id=artifact_id,
            artifact_name=artifact_name,
            description=None,
            museum_location=None,
            artifact_location=None,
            image_url=None,
            isDisplay=True,  # Set to True as requested
            display_startDate=None,
            created_at=datetime.now(ZoneInfo("Asia/Singapore")),
            updated_at=datetime.now(ZoneInfo("Asia/Singapore"))
        )
        
        session.add(artifact)
        return artifact
    
    async def update_artifacts(self) -> dict:
        """
        Main method to update artifacts database with YOLO model labels
        
        Returns:
            Dictionary with update statistics
        """
        # Load model and get labels
        model_labels = self.get_model_labels()
        
        # Database operations
        async with AsyncSessionLocal() as session:
            try:
                # Get existing artifacts
                existing_artifacts = await self.get_existing_artifacts(session)
                
                # Find new artifacts to add
                new_artifacts = [
                    label for label in model_labels 
                    if label not in existing_artifacts
                ]
                
                # Create new artifacts
                created_artifacts = []
                for artifact_name in new_artifacts:
                    artifact = await self.create_artifact(session, artifact_name)
                    created_artifacts.append(artifact)
                    print(f"Created artifact: {artifact_name} (ID: {artifact.id})")
                
                # Commit changes
                await session.commit()
                
                # Return statistics
                stats = {
                    "total_model_labels": len(model_labels),
                    "existing_artifacts": len(existing_artifacts),
                    "new_artifacts_created": len(created_artifacts),
                    "created_artifact_names": [a.artifact_name for a in created_artifacts]
                }
                
                print(f"\n=== Artifact Update Complete ===")
                print(f"Total labels in model: {stats['total_model_labels']}")
                print(f"Existing artifacts in DB: {stats['existing_artifacts']}")
                print(f"New artifacts created: {stats['new_artifacts_created']}")
                if stats['created_artifact_names']:
                    print(f"Created artifacts: {', '.join(stats['created_artifact_names'])}")
                
                return stats
                
            except Exception as e:
                await session.rollback()
                print(f"Error updating artifacts: {e}")
                raise
