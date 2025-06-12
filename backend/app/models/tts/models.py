from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple


class SegmentModel(BaseModel):
    """Represents a segment of a video with timing and text information."""
    start_time: float = Field(..., description="Start time of the segment in seconds")
    end_time: float = Field(..., description="End time of the segment in seconds")
    text: str = Field(default="", description="Text content of the segment")
    duration: Optional[float] = Field(None, description="Duration of the segment in seconds")
    is_silence: bool = Field(default=False, description="Whether this is a silent segment")


class VideoModel(BaseModel):
    """Represents a video with its metadata and segments."""
    title: str = Field(..., description="Title of the video")
    file_path: str = Field(..., description="Path to the video file")
    duration: float = Field(..., description="Duration of the video in seconds")
    segments: List[SegmentModel] = Field(..., description="List of segments in the video")

class TranscriptSegment(BaseModel):
    """Represents a segment of transcript with timing information."""
    start_time: float = Field(..., description="Start time of the segment in seconds")
    end_time: float = Field(..., description="End time of the segment in seconds")
    text: str = Field(..., description="Text content of the segment")
    is_silence: bool = Field(False, description="Whether this is a silent segment")
    duration: Optional[float] = Field(None, description="Duration of the segment in seconds")


class VideoTranscript(BaseModel):
    """Represents a video with its transcript segments."""
    title: str = Field(..., description="Title of the video")
    file_path: str = Field(..., description="Path to the video file")
    duration: float = Field(0.0, description="Duration of the video in seconds")
    segments: List[TranscriptSegment] = Field(..., description="List of segments in the video")
    segment_count: Optional[int] = Field(None, description="Number of segments")


class TranscriptMetadata(BaseModel):
    """Metadata about a transcript."""
    video_duration: float = Field(0.0, description="Duration of the video")
    total_segments: int = Field(0, description="Total number of segments")
    total_segments_duration: float = Field(0.0, description="Total duration of all segments")
    processing_timestamp: Optional[str] = Field(None, description="When the transcript was processed")
    processing_notes: Optional[str] = Field(None, description="Notes about processing")
    segment_stats: Optional[Dict[str, Any]] = Field(None, description="Statistics about segments")


class TranscriptData(BaseModel):
    """Complete transcript data structure for a video project."""
    title: str = Field(..., description="Title of the video project")
    description: str = Field("", description="Description of the video project")
    is_public: bool = Field(False, description="Whether the project is public")
    videos: List[VideoTranscript] = Field(..., description="List of videos with their transcripts")
    metadata: Optional[TranscriptMetadata] = Field(None, description="Metadata about the transcript")


class TTSRequest(BaseModel):
    """Request model for TTS generation."""
    title: str = Field(
        ...,
        description="Title of the project.",
        example="My Video Project"
    )
    description: str = Field(
        default="",
        description="Description of the project.",
        example="Auto-generated video project"
    )
    is_public: bool = Field(
        default=False,
        description="Whether the project is public."
    )
    videos: List[VideoTranscript] = Field(
        ...,
        description="List of videos in the project with their segments."
    )
    job_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for this job."
    )
    voice: str = Field(
        default="default",
        description="Voice to use for TTS. Default is the model's default voice."
    )
    language: str = Field(
        default="en",
        description="Language code for TTS. Default is 'en' for English."
    )
    speed: float = Field(
        default=1.0,
        description="Speed of speech. 1.0 is normal speed."
    )


class TTSResponse(BaseModel):
    """Response model for TTS generation."""
    job_id: str
    concatenated_audio_path: str
    message: str
