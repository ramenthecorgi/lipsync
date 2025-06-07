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
    videos = relationship("Video", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project {self.title}>"

class Video(BaseModel, Base):
    __tablename__ = "videos"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=True)
    thumbnail_path = Column(String(512), nullable=True)
    duration = Column(Float, default=0.0)  # in seconds
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="uploaded")  # uploaded, processing, ready, error
    metadata = Column(JSON, nullable=True)  # Additional metadata as JSON
    
    # Relationships
    project = relationship("Project", back_populates="videos")
    segments = relationship("VideoSegment", back_populates="video", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Video {self.title}>"

class VideoSegment(BaseModel, Base):
    __tablename__ = "video_segments"
    
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(Float, nullable=False)  # in seconds
    end_time = Column(Float, nullable=False)  # in seconds
    text = Column(Text, nullable=True)  # Transcript text
    speaker = Column(String(100), nullable=True)
    is_edited = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=True)  # Additional metadata as JSON
    
    # Relationships
    video = relationship("Video", back_populates="segments")
    
    def __repr__(self):
        return f"<VideoSegment {self.id} ({self.start_time}s-{self.end_time}s)>"
