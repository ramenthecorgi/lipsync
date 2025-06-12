from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
import os
import shutil
import subprocess
import time
from pathlib import Path
import uuid
import torch
from TTS.api import TTS
import numpy as np
import soundfile as sf
import io
import logging
import sys
import json
from typing import List, Optional, Dict, Any, Tuple

# Import models from the new location
from app.models.tts.models import (
    TTSRequest,
)
from app.models.lipsync.models import (
    LipSyncFromTranscriptRequest,
    LipSyncFromTranscriptResponse,
    LipSyncRequest,
    LipSyncResponse
)

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

# Import Wav2Lip service
try:
    from services.wav2lip.service import Wav2LipService
    WAV2LIP_AVAILABLE = True
except ImportError:
    WAV2LIP_AVAILABLE = False
    logging.warning("Wav2Lip service not available. Lip-sync will be limited to basic audio muxing.")

from pydantic import BaseModel, Field # Added for new Pydantic models
from app.utils.audio_utils import concatenate_audio_ffmpeg, cleanup_temp_audio  # moved to utils

router = APIRouter()

def resolve_backend_path(path: str) -> str:
    """
    Resolve a path to a backend-relative path with leading slash.
    
    Args:
        path: The path to resolve. Can be:
            - Absolute path within backend directory -> converts to /relative/path
            - Path starting with / -> treated as relative to backend root
            - Relative path -> treated as relative to backend root
            
    Returns:
        str: Path relative to backend root with leading slash (e.g., "/output_videos/file.mp4")
    """
    if not path:
        return ""
        
    # Get backend directory
    backend_dir = Path(__file__).parent.parent.parent.parent  # Go up to backend/
    
    # If it's an absolute path within the backend directory
    path_obj = Path(path)
    if path_obj.is_absolute():
        try:
            # Convert to path relative to backend dir
            rel_path = path_obj.relative_to(backend_dir)
            return f"/{rel_path}"
        except ValueError:
            # Not within backend directory, treat as relative
            pass
    
    # Handle paths that might have leading slash
    clean_path = path.lstrip('/')
    
    # Join with backend directory and resolve
    resolved_path = (backend_dir / clean_path).resolve()
    
    # Verify the path is within the backend directory for security
    try:
        rel_path = resolved_path.relative_to(backend_dir)
        return f"/{rel_path}"
    except ValueError:
        raise ValueError(f"Path {path} resolves outside backend directory")


# --- Configuration for TTS --- 
# Assuming this file (videos.py) is at backend/app/api/routers/videos.py
# So BASE_DIR should be backend/
_CURRENT_FILE_DIR = Path(__file__).resolve().parent
BASE_DIR = _CURRENT_FILE_DIR.parent.parent.parent  # Should resolve to backend/

# Directory configuration
TEMP_AUDIO_DIR = BASE_DIR / "temp" / "audio"

# Ensure directories exist
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

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

@router.post("/generate-lipsync-from-transcript", response_model=LipSyncFromTranscriptResponse, tags=["lipsync"])
async def generate_lipsync_from_transcript(
    background_tasks: BackgroundTasks,
    request: LipSyncFromTranscriptRequest,
    test_mode: bool = Query(False, description="Enable test mode to bypass heavy processing")
):
    """
    Generate a lip-synced video from a video and transcript data.
    
    This endpoint combines TTS generation and lip-syncing in one call:
    1. Converts transcript segments to audio using TTS
    2. Combines the audio segments
    3. Applies lip-syncing to the video
    
    Set test_mode=true to bypass heavy processing and return a mock response.
    
    Returns the path to the generated video.
    """
    # Log incoming request details
    print("\n=== Incoming Request ===")
    print(f"Test mode: {test_mode}")
    print(f"Job ID: {request.job_id}")
    print(f"Video Path: {request.video_path}")
    print(f"Output Path: {request.output_path}")
    if request.transcript and request.transcript.videos:
        print(f"Video Segments: {len(request.transcript.videos[0].segments) if request.transcript.videos[0].segments else 0} segments")
    print(json.dumps(request.transcript.dict(), indent=2, ensure_ascii=False))
    print("======================\n")

    # Uncomment to test echoing input url    
    # if test_mode:
    #     print(f"[TEST MODE] Bypassing processing for job: {request.job_id}")
    #     print("[TEST MODE] Simulating 5-second processing delay...")
    #     import time
    #     time.sleep(2)  # Add 5-second delay
    #     print("[TEST MODE] Delay complete, returning mock response")
    #     return {
    #         "job_id": request.job_id or f"test_job_{uuid.uuid4().hex[:8]}",
    #         "output_path": request.video_path,
    #         "message": "Test mode: Processing bypassed with 5s delay"
    #     }

    try:
        if not request.transcript.videos or not request.transcript.videos[0].segments:
            raise HTTPException(
                status_code=400,
                detail="No valid video segments found in the transcript"
            )
        
        # Create a TTS request from the transcript data
        tts_request = TTSRequest(
            title=request.transcript.title,
            description=request.transcript.description,
            is_public=request.transcript.is_public,
            videos=[{
                "title": request.transcript.videos[0].title,
                "file_path": request.transcript.videos[0].file_path,
                "duration": request.transcript.videos[0].duration,
                "segments": [{
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "text": s.text,
                    "is_silence": s.is_silence
                } for s in request.transcript.videos[0].segments]
            }],
            job_id=request.job_id,
            voice="default",  # Using default voice
            language="en"     # Default to English
        )
        
        # Generate TTS audio
        tts_response = await generate_tts_audio(background_tasks, tts_request)
        
        # Create a lip-sync request - ensure video_path is a string
        # Remove leading slash if present to prevent joining issues
        video_path = request.video_path.lstrip('/')
        video_path = str(BASE_DIR / video_path)
        lipsync_request = LipSyncRequest(
            video_path=video_path,
            audio_path=tts_response.concatenated_audio_path,
            job_id=request.job_id,
            use_wav2lip=False,
        )
        
        # Generate lip-synced video
        return await generate_lipsync_endpoint(background_tasks, lipsync_request, test_mode=test_mode)
        
    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process lip-sync from transcript: {str(e)}"
        )


# --- API Endpoint for TTS Generation --- 
# Import models from their respective modules

async def generate_tts_audio(
    background_tasks: BackgroundTasks,
    request: TTSRequest,
):
    """
    Generates audio from text segments using Coqui TTS and concatenates them.
    This endpoint supports multiple languages and voices.
    
    This is a thin wrapper around the TTSService which contains the actual implementation.
    """
    from app.services.tts.service import tts_service
    
    try:
        return await tts_service.generate_tts_audio(
            request=request,
            background_tasks=background_tasks
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate TTS audio: {str(e)}"
        )

async def generate_lipsync_video(
    request: LipSyncRequest,
    test_mode: bool = False,
    **wav2lip_kwargs
) -> str:
    """
    Generate a lip-synced video by combining video with new audio.
    
    Args:
        request: LipSyncRequest object containing video_path, audio_path, and other parameters
        test_mode: If True, bypasses heavy processing
        **wav2lip_kwargs: Additional arguments to pass to Wav2Lip
        
    Returns:
        Path to the generated video file
    """
    try:
        
        # Resolve input paths relative to backend directory
        video_path = request.video_path
        audio_path = request.audio_path
        print(f"Generating lip-synced video from {video_path} with audio {audio_path}")
        
        # Verify input files exist
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Set default output path if not provided
        output_dir = os.path.abspath("output_videos")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate a consistent output filename based on input filenames
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        timestamp = int(time.time())
        output_filename = f"lipsync_{video_name}_{timestamp}.mp4"
        output_path = os.path.join(output_dir, output_filename)
       
        print(f"Output will be saved to: {output_path}")
        
        # Create a temporary output file in the same directory as the final output
        temp_output = f"{output_path}.temp.mp4"
        
        # Use Wav2Lip if available and not in test mode
        if request.use_wav2lip and WAV2LIP_AVAILABLE and not test_mode:
            try:
                print("Using Wav2Lip for lip-syncing...")
                wav2lip = Wav2LipService()
                temp_output = wav2lip.generate_lipsync(
                    video_path=video_path,
                    audio_path=audio_path,
                    output_path=temp_output,
                    **wav2lip_kwargs
                )
                print(f"Wav2Lip processing complete. Output at: {temp_output}")
            except Exception as e:
                print(f"Wav2Lip processing failed: {str(e)}")
                print("Falling back to basic audio muxing...")
        else:
            print("Using basic audio muxing (no lip-sync)")
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output files without asking
                '-i', video_path,  # Input video
                '-i', audio_path,  # Input audio
                '-c:v', 'copy',  # Copy video stream without re-encoding
                '-c:a', 'aac',  # Encode audio as AAC
                '-strict', 'experimental',
                '-map', '0:v:0',  # Use first video stream from first input
                '-map', '1:a:0',  # Use first audio stream from second input
                '-shortest',  # Finish encoding when the shortest input stream ends
                temp_output
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            
            # Run the command and capture output for debugging
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                error_msg = f"FFmpeg command failed with error:\n{result.stderr}"
                print(error_msg)
                raise RuntimeError(f"Failed to process video: {error_msg}")
        
        # Verify the output file was created
        if not os.path.exists(temp_output):
            raise RuntimeError("Failed to create output file")
            
        # Replace the original file if it exists
        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(temp_output, output_path)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"Failed to create output file at {output_path}")
            
        print(f"Successfully created video at {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error in generate_lipsync_video: {str(e)}")
        raise

async def generate_lipsync_endpoint(background_tasks: BackgroundTasks, request: LipSyncRequest, test_mode: bool = False):
    """
    Generate a lip-synced video from a source video and audio file.
    
    This endpoint uses Wav2Lip for high-quality lip-syncing when available.
    """
    try:
        # Prepare Wav2Lip parameters
        wav2lip_params = {
            'use_wav2lip': request.use_wav2lip,
            'face_det_batch_size': request.face_det_batch_size,
            'wav2lip_batch_size': request.wav2lip_batch_size,
            'resize_factor': request.resize_factor,
            'crop': request.crop,
            'rotate': request.rotate,
            'nosmooth': request.nosmooth,
            'fps': request.fps,
            'pads': request.pads,
            'static': request.static
        }
        
        # Generate lip-synced video
        output_path = await generate_lipsync_video(
            request=request,
            test_mode=test_mode,
            **wav2lip_params
        )
        
        # Schedule cleanup of temporary audio file if it exists
        if request.audio_path and os.path.exists(request.audio_path):
            background_tasks.add_task(
                cleanup_temp_audio,
                request.audio_path
            )
        
        # Return just the filename for the video
        filename = os.path.basename(output_path)
        print(f"Generated video filename: {filename}")

        return LipSyncResponse(
            job_id=str(uuid.uuid4()),
            output_path="/videos/" + filename,  # Just the filename, e.g., "lipsync_1234567890.mp4"
            message="Lip-sync generation completed successfully"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate lip-synced video: {str(e)}"
        )
