from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel, Base

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
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(String(512), nullable=True)  # URL to the video file on the backend
    transcription = Column(JSON, nullable=True)  # Flexible JSON blob for additional data
    
    def __repr__(self):
        return f"<VideoTemplate {self.title}>"