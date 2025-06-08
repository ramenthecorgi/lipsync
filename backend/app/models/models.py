from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import BaseModel, Base
from ..schemas import VideoProjectSchema

class User(BaseModel, Base):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    
    def __repr__(self):
        return f"<User {self.email}>"

class Project(BaseModel, Base):
    __tablename__ = "projects"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_public = Column(Boolean, default=False)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    
    def __repr__(self):
        return f"<Project {self.title}>"

class VideoTemplate(BaseModel, Base):
    __tablename__ = "video_templates"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # URL to the video file on the backend
    video_project: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)  # Validated against VideoProjectSchema
    
    @property
    def video_project_data(self) -> Optional[VideoProjectSchema]:
        """Get the video project data as a validated VideoProjectSchema object."""
        if self.video_project is None:
            return None
        return VideoProjectSchema.model_validate(self.video_project)
    
    @video_project_data.setter
    def video_project_data(self, value: Optional[VideoProjectSchema]) -> None:
        """Set the video project data from a VideoProjectSchema object."""
        self.video_project = value.model_dump() if value is not None else None
    
    def __repr__(self) -> str:
        return f"<VideoTemplate {self.title}>"
    
    def update_from_schema(self, schema: VideoProjectSchema) -> None:
        """Update the template from a VideoProjectSchema."""
        self.title = schema.title
        if schema.description is not None:
            self.description = schema.description
        self.transcription_data = schema