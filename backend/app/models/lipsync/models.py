from pydantic import BaseModel, Field
from typing import Optional, Tuple, List, Dict, Any
import uuid
from app.models.tts.models import TranscriptData

class LipSyncFromTranscriptRequest(BaseModel):
    """Request model for generating lip-synced video from transcript."""
    video_path: str = Field(..., description="Path to the input video file")
    transcript: TranscriptData = Field(..., description="Transcript data in JSON format")
    output_path: str = Field(..., description="Path to save the output video. DO NOT USE")
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Job ID for tracking")


class LipSyncFromTranscriptResponse(BaseModel):
    """Response model for lip-sync from transcript."""
    job_id: str
    output_path: str
    message: str


class LipSyncRequest(BaseModel):
    """Request model for lip-sync generation."""
    video_path: str = Field(..., description="Path to the input video file")
    audio_path: str = Field(..., description="Path to the audio file for lip-sync")
    output_path: Optional[str] = Field(None, description="Path to save the output video")
    use_wav2lip: bool = Field(True, description="Whether to use Wav2Lip for lip-syncing (if available)")
    face_det_batch_size: int = Field(1, description="Batch size for face detection")
    wav2lip_batch_size: int = Field(16, description="Batch size for Wav2Lip")
    resize_factor: int = Field(1, description="Reduce the resolution by this factor")
    crop: Optional[Tuple[int, int, int, int]] = Field(
        None,
        description="Crop video (top, bottom, left, right)"
    )
    rotate: bool = Field(False, description="Rotate video 90 degrees counter-clockwise")
    nosmooth: bool = Field(False, description="Disable smoothing of face detections")
    fps: float = Field(25.0, description="FPS of output video")
    pads: Tuple[int, int, int, int] = Field(
        (0, 10, 0, 0),
        description="Padding (top, bottom, left, right) for face detection"
    )
    static: bool = Field(False, description="Use first frame for all frames (for static images)")
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Job ID for tracking")


# Alias for backward compatibility
LipSyncResponse = LipSyncFromTranscriptResponse
