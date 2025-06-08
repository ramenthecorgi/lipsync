from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timezone
from enum import Enum

router = APIRouter()

# --- Pydantic Models ---
class VideoSegment(BaseModel):
    """Represents a single segment of the video with editable text"""
    id: str
    videoId: str
    order: int
    startTime: float
    endTime: float
    originalText: str

class VideoAspectRatio(str, Enum):
    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_1_1 = "1:1"
    RATIO_4_5 = "4:5"

class VideoTemplate(BaseModel):
    """Represents a video template"""
    id: str
    title: str
    description: Optional[str] = None
    thumbnailUrl: str
    duration: float  # in seconds
    createdAt: Optional[str] = None  # ISO date string
    updatedAt: Optional[str] = None  # ISO date string
    aspectRatio: Optional[VideoAspectRatio] = None

class ProjectInfo(BaseModel):
    """Additional project metadata"""
    lastEdited: str  # ISO date string
    version: str
    createdBy: str
    language: str  # e.g., 'en-US', 'es-ES'

class VideoProject(BaseModel):
    """Complete video project with all its segments and metadata"""
    video: VideoTemplate
    segments: List[VideoSegment]
    projectInfo: Optional[ProjectInfo] = None

# Mock data - Replace with database queries in production
TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "template_1",
        "title": "Standard 16:9",
        "description": "Standard widescreen format",
        "thumbnailUrl": "https://example.com/thumbnails/standard.jpg",
        "duration": 120.5,
        "aspectRatio": "16:9",
    },
    {
        "id": "template_2",
        "title": "Portrait 9:16",
        "description": "Mobile vertical format",
        "thumbnailUrl": "https://example.com/thumbnails/portrait.jpg",
        "duration": 60.0,
        "aspectRatio": "9:16",
    }
]

# Mock speakers
SPEAKERS = [
    {
        "id": "spk_1",
        "name": "Alex Johnson",
        "role": "Host",
        "avatarUrl": "https://randomuser.me/api/portraits/men/32.jpg",
        "voiceProfileId": "voice_alex_1"
    },
    {
        "id": "spk_2",
        "name": "Maria Garcia",
        "role": "Narrator",
        "avatarUrl": "https://randomuser.me/api/portraits/women/44.jpg",
        "voiceProfileId": "voice_maria_1"
    }
]

# --- Helper Functions ---
def generate_segments(template_id: str, duration: float) -> List[Dict[str, Any]]:
    """Generate mock segments for a template"""
    num_segments = max(3, int(duration / 10))  # Roughly one segment per 10 seconds
    segments = []
    
    for i in range(num_segments):
        segment_duration = duration / num_segments
        start_time = i * segment_duration
        end_time = start_time + segment_duration
        
        segment = {
            "id": f"seg_{template_id}_{i}",
            "videoId": template_id,
            "order": i,
            "startTime": round(start_time, 2),
            "endTime": round(end_time, 2),
            "originalText": f"This is segment {i+1} of the video template.",
        }
        segments.append(segment)
    
    return segments

# --- API Endpoints ---
@router.get("/", response_model=List[VideoTemplate])
async def list_templates():
    """
    List all available video templates.
    Returns basic information about each template.
    """
    return TEMPLATES

@router.get("/{template_id}", response_model=VideoProject)
async def get_template(template_id: str):
    """
    Get detailed information about a specific template, including segments and speakers.
    
    Args:
        template_id: The unique identifier of the template
        
    Returns:
        VideoProject: Complete project data including video, segments, and speakers
        
    Raises:
        HTTPException: If template is not found
    """
    # Find the template
    template = next((t for t in TEMPLATES if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Generate segments for this template
    segments = generate_segments(template_id, template["duration"])
    
    # Create the project info
    now = datetime.now(timezone.utc).isoformat()
    project_info = {
        "lastEdited": now,
        "version": "1.0.0",
        "createdBy": "system",
        "language": "en-US"
    }
    
    # Create the full project response
    project = {
        "video": template,
        "segments": segments,
        "projectInfo": project_info,
    }
    
    return project
