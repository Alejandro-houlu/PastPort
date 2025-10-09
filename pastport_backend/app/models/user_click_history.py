"""
User Click History model for tracking which artifacts users have clicked on
This helps populate the "Artifacts" tab in the chat interface
"""
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from ..database import Base


class UserClickHistory(Base):
    """Track user clicks on artifacts for the chat interface"""
    __tablename__ = "user_click_history"
    
    # Primary key - UUID for unique identification
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    artifact_id = Column(String(8), ForeignKey("artifacts.id"), nullable=False, index=True)
    
    # Metadata
    clicked_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Singapore")), nullable=False)
    source = Column(String(50), nullable=True)  # 'camera', 'search', etc.
    
    # Relationships
    user = relationship("User")
    artifact = relationship("Artifact")
    
    # Create composite index for efficient queries
    __table_args__ = (
        Index('idx_user_artifact_clicked', 'user_id', 'artifact_id', 'clicked_at'),
    )
    
    def to_dict(self):
        """Convert user click history to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "artifact_id": self.artifact_id,
            "clicked_at": self.clicked_at,
            "source": self.source
        }
