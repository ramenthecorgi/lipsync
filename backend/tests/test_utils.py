import os
import cv2
import json
import numpy as np
import whisper
from pathlib import Path
from pydub import AudioSegment
from typing import Tuple, Dict, List, Optional
from moviepy.editor import VideoFileClip
from datetime import timedelta
import torch

class TestMediaGenerator:
    def __init__(self, base_dir: str = "test_assets"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
    def create_test_video(
        self, 
        filename: str = "test_video.mp4",
        duration: int = 5, 
        fps: int = 30,
        size: Tuple[int, int] = (640, 480),
        force_recreate: bool = False
    ) -> str:
        """Create a test video file with a colored background and text.
        
        Args:
            filename: Output filename
            duration: Duration in seconds
            fps: Frames per second
            size: Video dimensions (width, height)
            force_recreate: If True, recreate the file even if it exists
            
        Returns:
            Path to the created video file
        """
        output_path = self.base_dir / filename
        
        # Return existing file if it exists and we're not forcing recreation
        if output_path.exists() and not force_recreate:
            print(f"Using existing test video: {output_path}")
            return str(output_path)
            
        print(f"Creating new test video: {output_path}")
        width, height = size
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        for i in range(duration * fps):
            # Create a frame with a color that changes over time
            color = (i % 255, (i * 2) % 255, (i * 3) % 255)
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = color
            
            # Add some text
            text = f"Test Frame {i+1}"
            cv2.putText(frame, text, (50, height//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(frame)
        
        out.release()
        return str(output_path)
    
    def create_test_audio(
        self,
        filename: str = "test_audio.wav",
        duration: int = 5,
        sample_rate: int = 44100,
        freq: int = 440,
        force_recreate: bool = False
    ) -> str:
        """Create a test audio file with a sine wave tone.
        
        Args:
            filename: Output filename
            duration: Duration in seconds
            sample_rate: Audio sample rate
            freq: Frequency of the test tone
            force_recreate: If True, recreate the file even if it exists
            
        Returns:
            Path to the created audio file
        """
        output_path = self.base_dir / filename
        
        # Return existing file if it exists and we're not forcing recreation
        if output_path.exists() and not force_recreate:
            print(f"Using existing test audio: {output_path}")
            return str(output_path)
            
        print(f"Creating new test audio: {output_path}")
        
        # Generate a simple sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(2 * np.pi * freq * t) * 0.5  # 440Hz sine wave
        audio = (tone * 32767).astype(np.int16)  # Convert to 16-bit PCM
        
        # Create audio segment and export
        audio_segment = AudioSegment(
            audio.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 16-bit
            channels=1
        )
        audio_segment.export(str(output_path), format="wav")
        return str(output_path)
    
    def cleanup(self):
        """Remove all test files and directory.
        
        Note: This is now a no-op since we want to keep test files between runs.
        Override this method if you want to clean up files.
        """
        print("Skipping cleanup - test files are preserved between runs")


class VideoProcessor:
    def __init__(self, model_name: str = "base"):
        """Initialize the video processor with a Whisper model.
        
        Args:
            model_name: Name of the Whisper model to use (tiny, base, small, medium, large)
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model {model_name} on {self.device}...")
        self.model = whisper.load_model(model_name, device=self.device)
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Extract audio from a video file.
        
        Args:
            video_path: Path to the input video file
            output_path: Path to save the extracted audio (optional)
            
        Returns:
            Path to the extracted audio file
        """
        video_path = Path(video_path)
        if output_path is None:
            output_path = video_path.with_suffix('.wav')
        
        print(f"Extracting audio from {video_path}...")
        video = VideoFileClip(str(video_path))
        audio = video.audio
        audio.write_audiofile(str(output_path), logger=None)
        video.close()
        
        return str(output_path)
    
    def transcribe_audio(self, audio_path: str) -> Dict:
        """Transcribe audio using Whisper.
        
        Args:
            audio_path: Path to the audio file to transcribe
            
        Returns:
            Dictionary containing the transcription result
        """
        print(f"Transcribing audio: {audio_path}")
        result = self.model.transcribe(
            audio_path,
            verbose=True,
            language="en",
            word_timestamps=True
        )
        return result
    
    def _combine_segments(self, segments: List[Dict], target_count: int = 10) -> List[Dict]:
        """Combine segments into approximately equal-length segments.
        
        Args:
            segments: List of segment dictionaries
            target_count: Desired number of output segments
            
        Returns:
            List of combined segments
        """
        if not segments or target_count <= 0:
            return segments
            
        total_segments = len(segments)
        if total_segments <= target_count:
            return segments
            
        # Calculate how many segments to combine into each output segment
        segments_per_output = total_segments / target_count
        combined_segments = []
        
        i = 0
        while i < total_segments:
            # Calculate how many segments to combine for this output segment
            end_idx = min(round((len(combined_segments) + 1) * segments_per_output), total_segments)
            current_batch = segments[i:end_idx]
            
            if not current_batch:
                break
                
            # Combine the segments
            combined = {
                'start_time': current_batch[0]['start_time'],
                'end_time': current_batch[-1]['end_time'],
                'text': ' '.join(seg['text'].strip() for seg in current_batch if seg['text'].strip())
            }
            
            combined_segments.append(combined)
            i = end_idx
            
        return combined_segments

    def generate_transcript_json(self, video_path: str, max_segments: int = 5) -> Dict:
        """Generate a transcript JSON following the Project data model.
        
        Args:
            video_path: Path to the input video file
            max_segments: Maximum number of segments to include in the output
            
        Returns:
            Dictionary containing the project data with transcript
        """
        # Extract audio
        audio_path = self.extract_audio(video_path)
        
        # Transcribe audio
        result = self.transcribe_audio(audio_path)
        
        # Format segments according to Project model (without word-level breakdown)
        segments = [
            {
                'start_time': segment['start'],
                'end_time': segment['end'],
                'text': segment['text'].strip()
            }
            for segment in result['segments']
        ]
        
        # Combine segments to have approximately max_segments
        combined_segments = self._combine_segments(segments, max_segments)
        
        # Create project data structure
        video_path = Path(video_path)
        project_data = {
            'title': video_path.stem,
            'description': f'Auto-generated from {video_path.name}',
            'is_public': False,
            'videos': [
                {
                    'title': video_path.stem,
                    'file_path': str(video_path),
                    'duration': result['segments'][-1]['end'] if result['segments'] else 0,
                    'segments': combined_segments
                }
            ]
        }
        
        return project_data
    
    def save_transcript(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Generate and save transcript as JSON in the test_assets directory.
        
        Args:
            video_path: Path to the input video file
            output_path: Path to save the transcript JSON (optional). If not provided,
                      saves to test_assets/{video_name}.json
            
        Returns:
            Path to the saved transcript JSON file
        """
        video_path = Path(video_path)
        
        # Create test_assets directory if it doesn't exist
        test_assets_dir = Path("test_assets")
        test_assets_dir.mkdir(exist_ok=True)
        
        # Set default output path if not provided
        if output_path is None:
            output_path = test_assets_dir / f"{video_path.stem}.json"
        else:
            output_path = Path(output_path)
            # If output_path is a directory, use video name with .json extension
            if output_path.is_dir() or output_path.suffix != '.json':
                output_path = output_path / f"{video_path.stem}.json"
        
        # Ensure parent directories exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate and save transcript
        project_data = self.generate_transcript_json(str(video_path))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        print(f"Transcript saved to: {output_path.absolute()}")
        return str(output_path.absolute())


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_utils.py <video_file> [output_json]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Process video and generate transcript
    processor = VideoProcessor(model_name="base")
    json_path = processor.save_transcript(video_path, output_path)
    
    print(f"\nTranscript saved to: {json_path}")
