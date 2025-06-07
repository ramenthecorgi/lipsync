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
class TTSRequest(BaseModel):
    template_video_path: str = Field(
        ..., 
        description="Path to the template video (used for context, not processed in this phase).",
        example="/path/to/some/dummy_video.mp4"
    )
    transcript_segments: List[str] = Field(
        ..., 
        description="List of text segments to convert to speech.",
        example=["Hello world, this is the first sentence.", "This is the second sentence."]
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
            tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=torch.cuda.is_available())
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Coqui TTS initialization failed: {str(e)}")

    job_temp_segments_dir = TEMP_AUDIO_DIR / request.job_id
    try:
        job_temp_segments_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e_mkdir:
        raise HTTPException(status_code=500, detail=f"Could not create temporary directory for audio segments: {e_mkdir}")
    
    segment_audio_paths = []
    all_segments_processed_successfully = True

    for i, segment_text in enumerate(request.transcript_segments):
        if not segment_text.strip():
            print(f"Job {request.job_id}: Skipping empty transcript segment {i+1}")
            continue
            
        segment_output_path = job_temp_segments_dir / f"segment_{i+1}.wav"
        
        try:
            print(f"Job {request.job_id}: Generating TTS for segment {i+1}...")
            
            # Generate audio using Coqui TTS
            tts_kwargs = {
                'text': segment_text,
                # 'language': request.language,
                'speed': request.speed
            }
            
            audio = tts.tts(**tts_kwargs)
            
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

