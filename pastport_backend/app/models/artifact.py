"""
Artifact model for PastPort museum artifacts system
Manages museum artifact information and display status
"""
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, String, Boolean, DateTime, Text

from ..database import Base


class Artifact(Base):
    __tablename__ = "artifacts"
    
    # Primary key - 8-character UUID for unique identification
    id = Column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    
    # Artifact information fields
    artifact_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    museum_location = Column(String(255), nullable=True)
    artifact_location = Column(String(255), nullable=True)
    image_url = Column(String(500), nullable=True)
    
    # Display status fields
    isDisplay = Column(Boolean, default=False)
    display_startDate = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")))
    updated_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")), onupdate=lambda: datetime.now(ZoneInfo("Asia/Singapore")))
    
    def to_dict(self):
        """Convert artifact to dictionary for API responses"""
        return {
            "id": self.id,
            "artifact_name": self.artifact_name,
            "description": self.description,
            "museum_location": self.museum_location,
            "artifact_location": self.artifact_location,
            "image_url": self.image_url,
            "isDisplay": self.isDisplay,
            "display_startDate": self.display_startDate,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
