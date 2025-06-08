from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.orm import Session

from app.models.models import VideoTemplate as VideoTemplateModel
from app.database import get_db
from app.schemas import VideoProjectSchema, VideoAssetSchema

router = APIRouter()

class VideoAspectRatio(str, Enum):
    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_1_1 = "1:1"
    RATIO_4_5 = "4:5"

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
@router.get("/", response_model=List[VideoProjectSchema])
async def list_templates():
    """
    List all available video templates.
    Returns basic information about each template.
    """
    return TEMPLATES

@router.get("/{template_id}", response_model=VideoProjectSchema)
async def get_template(
    template_id: Union[int, str],  # Accept both int (DB ID) and str (for backward compatibility)
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific template, including segments and metadata.
    
    Args:
        template_id: The unique identifier of the template
        
    Returns:
        VideoProject: Complete project data including video, segments, and metadata
        
    Raises:
        HTTPException: If template is not found or has invalid data
    """
    # Query the database for the template
    try:
        # Try to convert to int if it's a string
        template_id_int = int(template_id) if isinstance(template_id, str) else template_id
        db_template = db.query(VideoTemplateModel).filter(VideoTemplateModel.id == template_id_int).first()
        if not db_template:
            raise HTTPException(status_code=404, detail="Template not found")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    # Get the video project data
    video_project_data = db_template.video_project_data
    if not video_project_data:
        raise HTTPException(status_code=400, detail="No video project data available for this template")
    
    # Extract segments and video assets from the video project data
    segments = []
    video_assets = []
    
    if video_project_data.videos:
        for video in video_project_data.videos:
            # Add video to assets
            video_assets.append({
                "title": video.title,
                "file_path": video.file_path,
                "duration": video.duration,
                "segments": [
                    {
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "text": segment.text,
                        "is_silence": segment.is_silence
                    }
                    for segment in video.segments
                ]
            })
            
            # Add segments to the segments list
            segments.extend([
                {
                    "id": f"{video.title}_{i}",
                    "videoId": video.title,
                    "order": i,
                    "startTime": segment.start_time,
                    "endTime": segment.end_time,
                    "originalText": segment.text
                }
                for i, segment in enumerate(video.segments)
            ])
    
    # Create project info
    project_info = {
        "lastEdited": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "createdBy": "system",
        "language": getattr(video_project_data.metadata, "language", "en-US") if video_project_data.metadata else "en-US"
    }
    
    # Return the complete project data
    return {
        "video": {
            "id": str(db_template.id),
            "title": db_template.title,
            "description": db_template.description,
            "thumbnailUrl": "",
            "duration": video_project_data.metadata.video_duration if video_project_data.metadata else 0,
            "createdAt": db_template.created_at.isoformat() if db_template.created_at else None,
            "updatedAt": db_template.updated_at.isoformat() if db_template.updated_at else None,
            "aspectRatio": None
        },
        "segments": segments,
        "projectInfo": project_info,
        "videos": video_assets,
        "title": video_project_data.title,
        "description": video_project_data.description,
        "is_public": video_project_data.is_public,
        "metadata": video_project_data.metadata.model_dump() if video_project_data.metadata else {}
    }
