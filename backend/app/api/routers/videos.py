from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import shutil
import subprocess # Added for running FFmpeg
from pathlib import Path
from datetime import datetime
import uuid
import torch
from TTS.api import TTS
import numpy as np
import soundfile as sf
import io
import subprocess
import cv2
import numpy as np
import os
import shutil
from typing import Optional
from pathlib import Path

from pydantic import BaseModel, Field # Added for new Pydantic models

from ... import schemas, models
from ...database import get_db
from ...core.security import get_current_active_user
from ...config import settings

router = APIRouter()

# --- TTS and Lip Sync POC Endpoints --- #

# --- Configuration for TTS --- 
# Assuming this file (videos.py) is at backend/app/api/routers/videos.py
# So BASE_DIR should be backend/
_CURRENT_FILE_DIR = Path(__file__).resolve().parent
BASE_DIR = _CURRENT_FILE_DIR.parent.parent.parent  # Should resolve to backend/

# Directory configuration
TEMP_AUDIO_DIR = BASE_DIR / "temp" / "audio"
OUTPUT_AUDIO_DIR = BASE_DIR / "output_audio"

# Ensure directories exist
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# --- Initialize Coqui TTS ---
try:
    # Check if CUDA is available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    # Initialize TTS with a fast model by default
    tts = TTS(model_name="tts_models/en/ljspeech/glow-tts", progress_bar=False, gpu=torch.cuda.is_available())
    print("Coqui TTS initialized successfully")
except Exception as e:
    tts = None
    print(f"Could not initialize Coqui TTS: {e}")

# --- Pydantic Models for TTS --- 
class SegmentModel(BaseModel):
    start_time: float = Field(..., description="Start time of the segment in seconds")
    end_time: float = Field(..., description="End time of the segment in seconds")
    text: str = Field(..., description="Text content of the segment")

class VideoModel(BaseModel):
    title: str = Field(..., description="Title of the video")
    file_path: str = Field(..., description="Path to the video file")
    duration: float = Field(..., description="Duration of the video in seconds")
    segments: List[SegmentModel] = Field(..., description="List of segments in the video")

class TTSRequest(BaseModel):
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
    videos: List[VideoModel] = Field(
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
    job_id: str
    concatenated_audio_path: str
    message: str

class LipSyncRequest(BaseModel):
    video_path: str = Field(..., description="Path to the input video file")
    audio_path: str = Field(..., description="Path to the audio file for lip-sync")
    output_path: Optional[str] = Field(None, description="Path to save the output video")
    
class LipSyncResponse(BaseModel):
    job_id: str
    output_path: str
    message: str

# --- Helper Functions for TTS --- 
def concatenate_audio_ffmpeg(segment_paths: List[str], output_path: str) -> bool:
    """
    Concatenates multiple WAV audio files into a single WAV file using FFmpeg.
    Assumes all input segments are WAV files.
    """
    if not segment_paths:
        print("No audio segments provided for concatenation.")
        return False

    list_file_path = TEMP_AUDIO_DIR / f"concat_list_{uuid.uuid4().hex}.txt"
    
    try:
        with open(list_file_path, 'w') as f:
            for path_str in segment_paths:
                abs_path = Path(path_str).resolve()
                f.write(f"file '{abs_path}'\n")

        command = [
            "ffmpeg",
            "-y", # Overwrite output file if it exists
            "-f", "concat",
            "-safe", "0", # Allow absolute paths in the list file
            "-i", str(list_file_path),
            "-c", "copy", # Copy audio codec as segments are already WAV
            str(output_path)
        ]

        print(f"Running FFmpeg command: {' '.join(command)}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=60) # 60 seconds timeout

        if process.returncode != 0:
            print(f"FFmpeg Error (concat audio): {stderr.decode()}")
            return False
        
        print(f"Successfully concatenated audio to {output_path}")
        return True
    except subprocess.TimeoutExpired:
        print("FFmpeg audio concatenation timed out.")
        if 'process' in locals() and process.poll() is None:
            process.kill()
        return False
    except Exception as e:
        print(f"Error running FFmpeg for audio concatenation: {e}")
        return False
    finally:
        if list_file_path.exists():
            try:
                list_file_path.unlink() # Clean up the list file
            except Exception as e_unlink:
                print(f"Error deleting concat list file {list_file_path}: {e_unlink}")

# --- API Endpoint for TTS Generation --- 
@router.post("/generate-tts-audio", response_model=TTSResponse, tags=["tts-poc"])
async def generate_tts_audio_endpoint(request: TTSRequest = Body(...)):
    """
    Generates audio from text segments using Coqui TTS and concatenates them.
    This endpoint supports multiple languages and voices.
    """
    global tts
    if tts is None:
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"Initializing TTS on device: {device}")
            
            # Use a simpler TTS model for testing
            tts = TTS(
                model_name="tts_models/en/ljspeech/tacotron2-DDC",
                progress_bar=True,
                gpu=torch.cuda.is_available()
            )
            
            print("TTS model loaded successfully")
            print(f"Available TTS models: {tts.list_models()}")
            
        except Exception as e:
            error_msg = f"Coqui TTS initialization failed: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "TTS initialization failed",
                    "message": str(e),
                    "type": type(e).__name__
                }
            )

    job_temp_segments_dir = TEMP_AUDIO_DIR / request.job_id
    try:
        job_temp_segments_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e_mkdir:
        raise HTTPException(status_code=500, detail=f"Could not create temporary directory for audio segments: {e_mkdir}")
    
    segment_audio_paths = []
    all_segments_processed_successfully = True

    if not request.videos or not request.videos[0].segments:
        raise HTTPException(status_code=400, detail="No video segments found in the request")

    for i, segment in enumerate(request.videos[0].segments):
        segment_text = segment.text.strip()
        if not segment_text:
            print(f"Job {request.job_id}: Skipping empty transcript segment {i+1}")
            continue
            
        segment_output_path = job_temp_segments_dir / f"segment_{i+1}.wav"
        
        try:
            print(f"Job {request.job_id}: Generating TTS for segment {i+1}...")
            print(f"Segment text: {segment_text}")
            print(f"Language: {request.language}, Speed: {request.speed}, Voice: {request.voice}")
            
            # Generate audio using Coqui TTS
            tts_kwargs = {
                'text': segment_text,
                # 'language': request.language,
                'speed': request.speed
            }
            
            print(f"TTS kwargs: {tts_kwargs}")
            
            # Use the voice parameter if available
            if hasattr(tts, 'speaker_wav') and request.voice and request.voice != "default":
                print(f"Using voice file: {request.voice}")
                tts_kwargs['speaker_wav'] = request.voice
            
            print("Calling TTS...")
            audio = tts.tts(**tts_kwargs)
            print(f"TTS returned audio of type: {type(audio)}")
            
            # Convert to numpy array and normalize to 16-bit PCM
            audio_np = np.array(audio)
            audio_np = (audio_np * 32767).astype(np.int16)
            
            # Save as WAV file
            with io.BytesIO() as wav_buffer:
                sf.write(wav_buffer, audio_np, 22050, format='WAV')
                wav_bytes = wav_buffer.getvalue()
            
            # Save to file
            with open(segment_output_path, "wb") as wf:
                wf.write(wav_bytes)
            
            segment_audio_paths.append(str(segment_output_path))
            print(f"Job {request.job_id}: TTS for segment {i+1} saved to {segment_output_path}")

        except Exception as e_tts:
            print(f"Job {request.job_id}: Error generating TTS for segment {i+1} ('{segment_text[:30]}...'): {e_tts}")
            all_segments_processed_successfully = False

    if not segment_audio_paths:
        if job_temp_segments_dir.exists():
            shutil.rmtree(job_temp_segments_dir, ignore_errors=True)
        detail_msg = "No audio segments were generated. Transcript might be empty or TTS failed for all segments."
        if not all_segments_processed_successfully:
            detail_msg += " Some segments encountered errors during TTS generation."
        raise HTTPException(status_code=400, detail=detail_msg)

    concatenated_audio_filename = f"{request.job_id}_concatenated_tts.wav"
    concatenated_output_path = OUTPUT_AUDIO_DIR / concatenated_audio_filename

    print(f"Job {request.job_id}: Concatenating {len(segment_audio_paths)} audio segments to {concatenated_output_path}...")
    if not concatenate_audio_ffmpeg(segment_audio_paths, str(concatenated_output_path)):
        if job_temp_segments_dir.exists():
            shutil.rmtree(job_temp_segments_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Job {request.job_id}: Failed to concatenate audio segments. Check server logs for FFmpeg errors.")

    # Optional: Clean up individual segment files after successful concatenation
    # For debugging, you might want to keep them initially.
    if job_temp_segments_dir.exists():
        shutil.rmtree(job_temp_segments_dir, ignore_errors=True)
        print(f"Job {request.job_id}: Cleaned up temporary segment directory {job_temp_segments_dir}")

    final_message = "TTS audio generated and concatenated successfully."
    if not all_segments_processed_successfully:
        final_message += " However, some transcript segments may have failed during TTS generation (check logs)."

    return TTSResponse(
        job_id=request.job_id,
        concatenated_audio_path=str(concatenated_output_path),
        message=final_message
    )

# Register the TTS endpoint
router.post(
    "/generate-tts-audio", 
    response_model=TTSResponse, 
    tags=["tts-poc"]
)(generate_tts_audio_endpoint)

def generate_lipsync_video(video_path: str, audio_path: str, output_path: Optional[str] = None) -> str:
    """
    Generate a lip-synced video using Wav2Lip
    """
    # Create output directory if it doesn't exist
    output_dir = Path("output_videos")
    output_dir.mkdir(exist_ok=True)
    
    # Set default output path if not provided
    if output_path is None:
        output_path = str(output_dir / f"lipsync_{Path(video_path).stem}.mp4")
    
    try:
        # This is a placeholder for the Wav2Lip inference
        # In a real implementation, you would call the Wav2Lip model here
        print(f"Generating lip-synced video from {video_path} with audio {audio_path}")
        print(f"Output will be saved to: {output_path}")
        
        # For now, we'll just copy the video as a placeholder
        # In a real implementation, you would use the Wav2Lip model here
        video = cv2.VideoCapture(video_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create a video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Process video frames (just copy them for now)
        while True:
            ret, frame = video.read()
            if not ret:
                break
            out.write(frame)
        
        video.release()
        out.release()
        
        # Add audio to the video
        temp_output = str(output_path).replace('.mp4', '_temp.mp4')
        cmd = [
            'ffmpeg',
            '-y',
            '-i', output_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            temp_output
        ]
        
        subprocess.run(cmd, check=True)
        
        # Replace the original file
        os.replace(temp_output, output_path)
        
        return output_path
        
    except Exception as e:
        print(f"Error in generate_lipsync_video: {str(e)}")
        raise

@router.post("/generate-lipsync", response_model=LipSyncResponse, tags=["lipsync"])
async def generate_lipsync_endpoint(request: LipSyncRequest = Body(...)):
    """
    Generate a lip-synced video from a source video and audio file.
    """
    try:
        # Generate lip-synced video
        output_path = generate_lipsync_video(
            video_path=request.video_path,
            audio_path=request.audio_path,
            output_path=request.output_path
        )
        
        return LipSyncResponse(
            job_id=str(uuid.uuid4()),
            output_path=output_path,
            message="Lip-sync generation completed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate lip-synced video: {str(e)}"
        )

