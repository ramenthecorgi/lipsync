from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime
import uuid

from ... import schemas, models
from ...database import get_db
from ...core.security import get_current_active_user
from ...config import settings

router = APIRouter()

def save_upload_file(upload_file: UploadFile, destination: Path) -> str:
    """Save uploaded file to the destination directory."""
    try:
        # Create a unique filename to avoid collisions
        file_extension = Path(upload_file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = destination / unique_filename
        
        # Ensure the directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return str(file_path.relative_to(settings.UPLOAD_DIR))
    finally:
        upload_file.file.close()

@router.post("/upload/", response_model=schemas.Video)
async def upload_video(
    project_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Upload a new video file."""
    # Check if project exists and user has access
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied")
    
    # Validate file type
    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv"}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Save the file
    upload_dir = Path(settings.UPLOAD_DIR)
    file_path = save_upload_file(file, upload_dir)
    
    # Create video record in database
    db_video = models.Video(
        title=title,
        description=description,
        file_path=str(file_path),
        project_id=project_id,
        status="uploaded",
    )
    
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    # In a real application, you would start background tasks for video processing here
    # e.g., generate_thumbnails.delay(db_video.id)
    # e.g., extract_audio.delay(db_video.id)
    # e.g., transcribe_video.delay(db_video.id)
    
    return db_video

@router.get("/{video_id}", response_model=schemas.Video)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get video by ID."""
    video = db.query(models.Video).join(models.Project).filter(
        models.Video.id == video_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found or access denied")
        
    return video

@router.get("/project/{project_id}", response_model=List[schemas.Video])
def get_videos_by_project(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get all videos for a specific project."""
    # Verify project exists and user has access
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied")
    
    videos = db.query(models.Video).filter(
        models.Video.project_id == project_id
    ).offset(skip).limit(limit).all()
    
    return videos

@router.put("/{video_id}", response_model=schemas.Video)
def update_video(
    video_id: int,
    video_update: schemas.VideoUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Update video metadata."""
    video = db.query(models.Video).join(models.Project).filter(
        models.Video.id == video_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found or access denied")
    
    # Update video fields
    update_data = video_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(video, field, value)
    
    video.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(video)
    
    return video

@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Delete a video."""
    video = db.query(models.Video).join(models.Project).filter(
        models.Video.id == video_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found or access denied")
    
    # Delete the file if it exists
    if video.file_path:
        try:
            file_path = Path(settings.UPLOAD_DIR) / video.file_path
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error deleting file {video.file_path}: {e}")
    
    # Delete the video record
    db.delete(video)
    db.commit()
    
    return None

# Video Segments Endpoints
@router.post("/{video_id}/segments/", response_model=schemas.VideoSegment)
def create_video_segment(
    video_id: int,
    segment: schemas.VideoSegmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Create a new segment for a video."""
    # Verify video exists and user has access
    video = db.query(models.Video).join(models.Project).filter(
        models.Video.id == video_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found or access denied")
    
    # Create the segment
    db_segment = models.VideoSegment(
        **segment.dict(),
        video_id=video_id
    )
    
    db.add(db_segment)
    db.commit()
    db.refresh(db_segment)
    
    return db_segment

@router.get("/{video_id}/segments/", response_model=List[schemas.VideoSegment])
def get_video_segments(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get all segments for a video."""
    # Verify video exists and user has access
    video = db.query(models.Video).join(models.Project).filter(
        models.Video.id == video_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found or access denied")
    
    # Get all segments for the video
    segments = db.query(models.VideoSegment).filter(
        models.VideoSegment.video_id == video_id
    ).order_by(models.VideoSegment.start_time).all()
    
    return segments

@router.put("/segments/{segment_id}", response_model=schemas.VideoSegment)
def update_video_segment(
    segment_id: int,
    segment_update: schemas.VideoSegmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Update a video segment."""
    # Get the segment with video and project info
    segment = (
        db.query(models.VideoSegment)
        .join(models.Video)
        .join(models.Project)
        .filter(
            models.VideoSegment.id == segment_id,
            models.Project.owner_id == current_user.id
        )
        .first()
    )
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found or access denied")
    
    # Update segment fields
    update_data = segment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(segment, field, value)
    
    segment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(segment)
    
    return segment

@router.delete("/segments/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video_segment(
    segment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Delete a video segment."""
    # Get the segment with video and project info
    segment = (
        db.query(models.VideoSegment)
        .join(models.Video)
        .join(models.Project)
        .filter(
            models.VideoSegment.id == segment_id,
            models.Project.owner_id == current_user.id
        )
        .first()
    )
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found or access denied")
    
    # Delete the segment
    db.delete(segment)
    db.commit()
    
    return None
