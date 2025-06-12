"""Service layer for Text-to-Speech (TTS) operations."""
import os
import uuid
import numpy as np
import torch
from pathlib import Path
from typing import List, Optional, Dict, Any
import soundfile as sf

from TTS.api import TTS
from fastapi import HTTPException

# Import models and utils
from app.models.tts.models import TTSRequest, TTSResponse, SegmentModel, VideoTranscript
from app.utils.audio_utils import concatenate_audio_ffmpeg, cleanup_temp_audio

# Configuration
TEMP_AUDIO_DIR = Path(__file__).parent.parent.parent / "temp" / "audio"
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class TTSService:
    """Service for handling Text-to-Speech operations."""
    
    def __init__(self):
        self.tts = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._initialize_tts()
    
    def _initialize_tts(self) -> None:
        """Initialize the TTS model."""
        try:
            print(f"Initializing TTS on device: {self.device}")
            
            print("Checking CUDA availability...")
            if torch.cuda.is_available():
                print(f"CUDA is available. Device count: {torch.cuda.device_count()}")
                print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
            else:
                print("CUDA is not available, using CPU")
            
            print("Initializing TTS model...")
            # Use a model that supports voice cloning
            self.tts = TTS(
                model_name="tts_models/multilingual/multi-dataset/your_tts",
                progress_bar=False,
                gpu=torch.cuda.is_available(),
                config_path=None,
                model_path=None,
            )
            
            if self.tts is None:
                print("TTS instance is None after initialization")
                raise RuntimeError("Failed to create TTS instance")
                
            print("TTS initialized successfully")
            
        except Exception as e:
            import traceback
            error_msg = f"Could not initialize TTS: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            print("TTS initialization failed. Model will be None.")
            self.tts = None
    
    async def generate_tts_audio(
        self,
        request: TTSRequest,
        background_tasks
    ) -> TTSResponse:
        """Generate TTS audio for the given request.
        
        Args:
            request: TTS request containing segments and configuration
            background_tasks: FastAPI background tasks for cleanup
            
        Returns:
            TTSResponse containing job ID and output path
            
        Raises:
            HTTPException: If TTS initialization fails or processing error occurs
        """
        if not self.tts:
            raise HTTPException(status_code=500, detail="TTS service not available")
            
        try:
            # Create temp directory for audio segments
            job_id = request.job_id or str(uuid.uuid4())
            temp_dir = TEMP_AUDIO_DIR / job_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            segment_audio_paths = []
            
            if not request.videos or not request.videos[0].segments:
                raise HTTPException(status_code=400, detail="No video segments found in the request")
            
            # Process each segment
            segments = self._prepare_segments(request.videos[0].segments)
            
            for i, segment in enumerate(segments):
                segment_path = await self._process_segment(
                    segment=segment,
                    segment_index=i,
                    temp_dir=temp_dir,
                    voice=request.voice,
                    speed=request.speed
                )
                if segment_path:
                    segment_audio_paths.append(str(segment_path))
            
            if not segment_audio_paths:
                raise HTTPException(status_code=400, detail="No valid segments to process")
            
            # Verify all segment files exist before concatenation
            for path in segment_audio_paths:
                if not os.path.exists(path):
                    raise HTTPException(
                        status_code=500,
                        detail=f"Segment file not found: {path}"
                    )
            
            # Concatenate all segments
            output_filename = f"tts_output_{job_id}.wav"
            output_path = str((temp_dir / output_filename).resolve())
            
            print(f"Concatenating {len(segment_audio_paths)} audio segments to {output_path}")
            if not concatenate_audio_ffmpeg(segment_audio_paths, output_path):
                raise HTTPException(status_code=500, detail="Failed to concatenate audio segments")
            
            # Verify output file was created
            if not os.path.exists(output_path):
                raise HTTPException(
                    status_code=500,
                    detail=f"Output file was not created: {output_path}"
                )
            
            # Schedule cleanup of temporary files
            background_tasks.add_task(self._cleanup_temp_files, temp_dir, segment_audio_paths)
            
            return TTSResponse(
                job_id=job_id,
                concatenated_audio_path=output_path,
                message="TTS audio generation completed successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
    
    def _prepare_segments(self, segments: List[SegmentModel]) -> List[Dict[str, Any]]:
        """Prepare segments with proper timings and durations."""
        prepared_segments = []
        for segment in segments:
            seg_dict = segment.dict()
            seg_dict['duration'] = segment.end_time - segment.start_time
            # Ensure minimum duration of 0.5s for very short segments
            if seg_dict['duration'] < 0.5:
                seg_dict['duration'] = 0.5
            prepared_segments.append(seg_dict)
        return prepared_segments
    
    async def _process_segment(
        self,
        segment: Dict[str, Any],
        segment_index: int,
        temp_dir: Path,
        voice: str,
        speed: float
    ) -> Optional[str]:
        """Process a single TTS segment."""
        if not segment.get('text', '').strip() or segment.get('is_silence', False):
            print(f"Skipping empty or silent segment {segment_index}")
            return None
            
        # Ensure the output directory exists
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = temp_dir / f"segment_{segment_index:04d}.wav"
        output_path_str = str(output_path.resolve())
        
        print(f"Processing segment {segment_index} -> {output_path_str}")
        
        try:
            tts_kwargs = {
                'text': segment['text'].strip(),
                'file_path': output_path_str,
                'speed': speed
            }
            
            # Handle different voice options
            print(f"\n=== TTS Generation Parameters ===")
            print(f"TTS Model: {self.tts.speakers if hasattr(self.tts, 'speakers') else 'No speakers available'}")
            print(f"Voice cloning supported: {hasattr(self.tts, 'speakers')}")
            print(f"Voice parameter received: {voice}")
            
            if voice and voice != 'default':
                if voice.endswith('.wav'):
                    if not os.path.exists(voice):
                        print(f"ERROR: Speaker WAV file not found: {voice}")
                    else:
                        print(f"Using voice cloning with audio file: {voice}")
                        print(f"File size: {os.path.getsize(voice) / 1024:.2f} KB")
                        tts_kwargs['speaker_wav'] = voice
                        # Add language parameter which is required for multilingual models
                        language = 'en'  # Default to English, adjust as needed
                        tts_kwargs['language'] = language
                        print(f"Using language: {language}")
                else:
                    tts_kwargs['speaker'] = voice
                    print(f"Using pre-trained voice: {voice}")
            else:
                print("Using default voice")
                
            print(f"Final TTS kwargs: {tts_kwargs}")
            print("===============================\n")
            
            print(f"Generating TTS for segment {segment_index} with text: {segment['text'][:50]}...")
            print(f"Output path: {output_path}")
            print(f"Parent directory exists: {output_path.parent.exists()}")
            print(f"Parent directory permissions: {oct(output_path.parent.stat().st_mode)}")
            
            # First check if we can write to the directory
            test_file = output_path.parent / "test_permission.txt"
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                print(f"Successfully wrote to test file: {test_file}")
            except Exception as perm_err:
                print(f"Error writing to test file: {perm_err}")
                raise PermissionError(f"Cannot write to directory: {output_path.parent}")
            finally:
                if test_file.exists():
                    test_file.unlink()
            
            # Generate TTS audio
            print("Starting TTS generation...")
            audio = self.tts.tts(**tts_kwargs)
            print("TTS generation completed")
            
            # Verify audio was generated
            if audio is None:
                raise ValueError("TTS returned None audio")
                
            # Save audio as WAV
            print("Saving audio as WAV...")
            sf.write(str(output_path), audio, 22050)
            print(f"Audio saved to: {output_path}")
            
            # Verify the file was created and has content
            if not output_path.exists():
                raise FileNotFoundError(f"TTS output file was not created: {output_path}")
                
            file_size = output_path.stat().st_size
            if file_size == 0:
                raise ValueError(f"TTS output file is empty: {output_path}")
                
            print(f"TTS output file created successfully: {output_path} (size: {file_size} bytes)")
            return output_path_str
            
        except Exception as e:
            import traceback
            error_msg = f"Error during TTS generation for segment {segment_index}: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception as cleanup_err:
                    print(f"Error cleaning up failed TTS output: {cleanup_err}")
            raise
    
    async def _cleanup_temp_files(self, temp_dir: Path, segment_paths: List[str]) -> None:
        """Clean up temporary files in the background."""
        print(f"Starting cleanup of temporary files in {temp_dir}")
        
        # Clean up individual segment files
        for path in segment_paths:
            try:
                if path and os.path.exists(path):
                    print(f"Removing temporary file: {path}")
                    cleanup_temp_audio(path)
                else:
                    print(f"Skipping non-existent file: {path}")
            except Exception as e:
                print(f"Error removing temporary file {path}: {e}")
        
        # Remove the temp directory if empty
        try:
            if temp_dir.exists():
                # Try to remove the directory (will only succeed if empty)
                try:
                    temp_dir.rmdir()
                    print(f"Removed empty directory: {temp_dir}")
                except OSError as e:
                    print(f"Could not remove directory (may not be empty): {temp_dir}, error: {e}")
                    # Optionally, remove directory and all its contents
                    # shutil.rmtree(temp_dir, ignore_errors=True)
                    # print(f"Removed directory and all contents: {temp_dir}")
        except Exception as e:
            print(f"Error during directory cleanup for {temp_dir}: {e}")
            
        print(f"Completed cleanup of temporary files in {temp_dir}")

# Create a singleton instance for dependency injection
tts_service = TTSService()
