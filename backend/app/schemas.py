from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    is_superuser: bool = False
    
    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

# Video schemas
class VideoStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration: Optional[float] = 0.0
    status: VideoStatus = VideoStatus.UPLOADED
    metadata: Optional[Dict[str, Any]] = None

class VideoCreate(VideoBase):
    project_id: int

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[VideoStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class Video(VideoBase):
    id: int
    project_id: int
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Video Segment schemas
class VideoSegmentBase(BaseModel):
    start_time: float
    end_time: float
    text: Optional[str] = None
    speaker: Optional[str] = None
    is_edited: bool = False
    metadata: Optional[Dict[str, Any]] = None

class VideoSegmentCreate(VideoSegmentBase):
    video_id: int

class VideoSegmentUpdate(BaseModel):
    text: Optional[str] = None
    speaker: Optional[str] = None
    is_edited: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class VideoSegment(VideoSegmentBase):
    id: int
    video_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Response models
class Message(BaseModel):
    detail: str

class HTTPError(BaseModel):
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {"detail": "Error message"}
        }

# Video Metadata Models
class SegmentStats(BaseModel):
    min_duration: float
    max_duration: float
    avg_duration: float
    silent_segments: int
    spoken_segments: int

class VideoMetadata(BaseModel):
    video_duration: float
    total_segments: int
    total_segments_duration: float
    processing_timestamp: int  # UNIX timestamp in milliseconds
    processing_notes: str
    segment_stats: SegmentStats
    
    @field_validator('processing_timestamp')
    def validate_timestamp(cls, v):
        if not isinstance(v, int) or v <= 0:
            raise ValueError('processing_timestamp must be a positive integer (UNIX timestamp in milliseconds)')
        return v

class VideoSegmentSchema(BaseModel):
    start_time: float
    end_time: float
    text: str
    is_silence: bool

    @field_validator('end_time')
    def validate_times(cls, v: float, info):
        if hasattr(info, 'data') and 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be greater than start_time')
        return v

class VideoAssetSchema(BaseModel):
    title: str
    file_path: str
    duration: float
    segments: List[VideoSegmentSchema]

class VideoProjectSchema(BaseModel):
    title: str
    description: Optional[str] = None
    is_public: bool
    metadata: VideoMetadata
    videos: List[VideoAssetSchema]