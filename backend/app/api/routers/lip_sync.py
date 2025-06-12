from fastapi import APIRouter, Body, HTTPException, Query
from typing import List, Optional, Dict, Any
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
from typing import Optional, Tuple, List, Dict, Any
import json
from pydantic import BaseModel

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

class TranscriptSegment(BaseModel):
    start_time: float = Field(..., description="Start time of the segment in seconds")
    end_time: float = Field(..., description="End time of the segment in seconds")
    text: str = Field(..., description="Text content of the segment")
    is_silence: bool = Field(False, description="Whether this is a silent segment")

class VideoTranscript(BaseModel):
    title: str = Field(..., description="Title of the video")
    file_path: str = Field(..., description="Path to the video file")
    duration: float = Field(0.0, description="Duration of the video in seconds")
    segments: List[TranscriptSegment] = Field(..., description="List of segments in the video")
    segment_count: Optional[int] = Field(None, description="Number of segments")

class TranscriptMetadata(BaseModel):
    video_duration: float = Field(0.0, description="Duration of the video")
    total_segments: int = Field(0, description="Total number of segments")
    total_segments_duration: float = Field(0.0, description="Total duration of all segments")
    processing_timestamp: Optional[str] = Field(None, description="When the transcript was processed")
    processing_notes: Optional[str] = Field(None, description="Notes about processing")
    segment_stats: Optional[Dict[str, Any]] = Field(None, description="Statistics about segments")

class TranscriptData(BaseModel):
    """Model for the transcript JSON structure."""
    title: str = Field(..., description="Title of the video project")
    description: str = Field("", description="Description of the video project")
    is_public: bool = Field(False, description="Whether the project is public")
    videos: List[VideoTranscript] = Field(..., description="List of videos with their transcripts")
    metadata: Optional[TranscriptMetadata] = Field(None, description="Metadata about the transcript")

class LipSyncFromTranscriptRequest(BaseModel):
    """Request model for generating lip-synced video from transcript."""
    video_path: str = Field(..., description="Path to the input video file")
    transcript: TranscriptData = Field(..., description="Transcript data in JSON format")
    output_path: str = Field(..., description="Path to save the output video. DO NOT USE")
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Job ID for tracking")

class LipSyncFromTranscriptResponse(BaseModel):
    job_id: str
    output_path: str
    message: str

@router.post("/generate-lipsync-from-transcript", response_model=LipSyncFromTranscriptResponse, tags=["lipsync"])
async def generate_lipsync_from_transcript(
    request: LipSyncFromTranscriptRequest = Body(...),
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
        tts_response = await generate_tts_audio_endpoint(tts_request)
        
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
        return await generate_lipsync_endpoint(lipsync_request, test_mode=test_mode)
        
    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process lip-sync from transcript: {str(e)}"
        )


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
# --- Pydantic Models for TTS --- 
class SegmentModel(BaseModel):
    start_time: float = Field(..., description="Start time of the segment in seconds")
    end_time: float = Field(..., description="End time of the segment in seconds")
    text: str = Field(default="", description="Text content of the segment")
    duration: Optional[float] = Field(None, description="Duration of the segment in seconds")
    is_silence: bool = Field(default=False, description="Whether this is a silent segment")

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

LipSyncResponse = LipSyncFromTranscriptResponse

# @router.post("/generate-tts-audio", response_model=TTSResponse, tags=["tts-poc"])
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

    # Use original segment timings to preserve natural pauses
    segments = request.videos[0].segments
    for i in range(len(segments)):
        # Calculate duration based on original video timing
        segment_dict = segments[i].dict()
        segment_dict['duration'] = segments[i].end_time - segments[i].start_time
        # Ensure minimum duration of 0.5s for very short segments
        if segment_dict['duration'] < 0.5:
            segment_dict['duration'] = 0.5
        segments[i] = SegmentModel(**segment_dict)
    
    # Helper for context-aware pause adjustment
    def get_natural_pause(prev_text, base_duration):
        import numpy as np
        if not prev_text:
            return base_duration
        prev_text = prev_text.strip()
        # Sentence-ending punctuation
        if prev_text.endswith(('.', '!', '?')):
            return max(base_duration, 0.7 + np.random.uniform(-0.1, 0.3))
        # Phrase-ending punctuation
        elif prev_text.endswith((',', ';', ':')):
            return max(base_duration, 0.3 + np.random.uniform(-0.05, 0.1))
        # Otherwise, keep short
        return max(base_duration, 0.15 + np.random.uniform(-0.03, 0.05))

    # Generate audio for each segment (both silent and spoken)
    for i, segment in enumerate(segments):
        segment_duration = segment.end_time - segment.start_time
        segment_output_path = job_temp_segments_dir / f"segment_{i+1:04d}.wav"
        
        try:
            print(f"\nJob {request.job_id}: Processing segment {i+1}/{len(segments)}")
            print(f"Type: {'SILENCE' if segment.is_silence else 'SPEECH'}")
            print(f"Timing: {segment.start_time:.2f}s - {segment.end_time:.2f}s ({segment_duration:.2f}s)")
            
            if segment.is_silence or not segment.text.strip():
                # Context-aware adjustment for silence duration
                prev_text = segments[i-1].text if i > 0 else ''
                natural_pause = get_natural_pause(prev_text, segment_duration)
                print(f"Generating {natural_pause:.2f}s of context-aware silence (original: {segment_duration:.2f}s)")
                silence_samples = int(natural_pause * 22050)
                audio_np = np.zeros(silence_samples, dtype=np.int16)
            else:
                # Generate TTS for spoken segment
                print(f"Text: {segment.text}")
                
                # Generate audio using Coqui TTS
                tts_kwargs = {
                    'text': segment.text.strip(),
                    'speed': request.speed
                }
                
                # Use the voice parameter if available
                if hasattr(tts, 'speaker_wav') and request.voice and request.voice != "default":
                    tts_kwargs['speaker_wav'] = request.voice
                
                print("Generating TTS audio...")
                audio = tts.tts(**tts_kwargs)
                
                # Convert to numpy array and normalize to 16-bit PCM
                audio_np = np.array(audio)
                audio_np = (audio_np * 32767).astype(np.int16)
                
                # Calculate current and target durations (in samples)
                current_samples = len(audio_np)
                target_samples = int(segment_duration * 22050)
                
                print(f"Generated audio: {current_samples/22050:.2f}s, Target: {segment_duration:.2f}s")
                
                if current_samples > target_samples:
                    # If audio is too long, truncate it
                    print(f"Truncating audio from {current_samples/22050:.2f}s to {segment_duration:.2f}s")
                    audio_np = audio_np[:target_samples]
                elif current_samples < target_samples:
                    # If audio is shorter, add silence at the end
                    silence_samples = target_samples - current_samples
                    print(f"Adding {silence_samples/22050:.2f}s of silence to match duration")
                    silence = np.zeros(silence_samples, dtype=np.int16)
                    audio_np = np.concatenate([audio_np, silence])
            
            # Save as WAV file
            with io.BytesIO() as wav_buffer:
                sf.write(wav_buffer, audio_np, 22050, format='WAV')
                wav_bytes = wav_buffer.getvalue()
            
            with open(segment_output_path, 'wb') as f:
                f.write(wav_bytes)
                
            segment_audio_paths.append(str(segment_output_path.absolute()))
            print(f"Saved segment {i+1} to {segment_output_path}")
            
        except Exception as e:
            print(f"Error processing segment {i+1}: {e}")
            import traceback
            traceback.print_exc()
            all_segments_processed_successfully = False
            break

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

async def generate_lipsync_endpoint(request: LipSyncRequest, test_mode: bool = False):
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

