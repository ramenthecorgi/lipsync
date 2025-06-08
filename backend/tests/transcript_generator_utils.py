import os
import cv2
import json
import numpy as np
import whisper
import datetime
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
        """Extract audio from a video file to a temporary file.
        
        Args:
            video_path: Path to the input video file
            output_path: Path to save the extracted audio (optional, uses temp file if None)
            
        Returns:
            Path to the extracted audio file (temporary file if output_path is None)
        """
        import tempfile
        
        video_path = Path(video_path)
        is_temp = output_path is None
        
        if is_temp:
            # Create a temporary file that will be automatically cleaned up when closed
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            output_path = temp_file.name
            temp_file.close()
        else:
            output_path = str(output_path)
        
        print(f"Extracting audio from {video_path}...")
        try:
            video = VideoFileClip(str(video_path))
            audio = video.audio
            audio.write_audiofile(output_path, logger=None, verbose=False)
            return output_path
        finally:
            video.close()
            if is_temp:
                # The file will be deleted when the process ends
                # or when the file object is garbage collected
                import atexit
                import os
                atexit.register(lambda: os.unlink(output_path) if os.path.exists(output_path) else None)
    
    def transcribe_audio(self, audio_path: str) -> Dict:
        """Transcribe audio using Whisper.
        
        Args:
            audio_path: Path to the audio file to transcribe
            
        Returns:
            Dictionary containing the transcription result
        """
        print(f"Transcribing audio: {audio_path}")
        try:
            result = self.model.transcribe(
                audio_path,
                verbose=True,
                language="en",
                word_timestamps=True
            )
            return result
        finally:
            # Clean up the temporary audio file if it exists
            try:
                import os
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary audio file: {e}")
    
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

    class SmartSegmentProcessor:
        def __init__(
            self,
            max_segments: int = 20,
            max_silence_duration: float = 0.5,
            min_segment_duration: float = 0.3,
        ):
            self.max_segments = max_segments
            self.max_silence_duration = max_silence_duration
            self.min_segment_duration = min_segment_duration

        def process_segments(self, segments: List[Dict], video_duration: float) -> List[Dict]:
            if not segments:
                return []

            # First pass: Add all silent segments
            processed = self._add_silent_segments(segments, video_duration)
            
            # Second pass: Merge short silences
            processed = self._merge_short_silences(processed)
            
            # Third pass: Ensure minimum segment duration
            return self._enforce_min_duration(processed)

        def _add_silent_segments(self, segments: List[Dict], video_duration: float) -> List[Dict]:
            """Add silent segments between and around spoken segments"""
            processed = []
            prev_end = 0.0

            for segment in segments:
                # Add leading silence if significant gap
                if segment['start_time'] > prev_end + self.max_silence_duration:
                    processed.append({
                        'start_time': prev_end,
                        'end_time': segment['start_time'],
                        'text': '',
                        'is_silence': True
                    })
                
                # Add the spoken segment
                processed.append(segment)
                prev_end = segment['end_time']
            
            # Add trailing silence if needed
            if prev_end < video_duration - self.max_silence_duration:
                processed.append({
                    'start_time': prev_end,
                    'end_time': video_duration,
                    'text': '',
                    'is_silence': True
                })
                
            return processed

        def _merge_short_silences(self, segments: List[Dict]) -> List[Dict]:
            """Merge short silences and consecutive non-silent segments"""
            if len(segments) <= 1:
                return segments

            result = [segments[0]]
            
            for current in segments[1:]:
                last = result[-1]
                
                # If current is a short silence, merge with adjacent segments
                if (current['is_silence'] and 
                    (current['end_time'] - current['start_time']) <= self.max_silence_duration):
                    
                    # Extend previous segment's end time
                    if not last['is_silence']:
                        last['end_time'] = current['end_time']
                    # Or extend next non-silent segment's start time
                    elif len(result) > 1:
                        result[-2]['end_time'] = current['end_time']
                        result.pop()
                    else:
                        result[-1] = current
                
                # Merge consecutive non-silent segments that are close together
                elif (not current['is_silence'] and not last['is_silence'] and
                      (current['start_time'] - last['end_time']) <= self.max_silence_duration):
                    # Merge the current segment with the previous one
                    last['end_time'] = current['end_time']
                    last['text'] = ' '.join(filter(None, [last.get('text', ''), current.get('text', '')]))
                
                else:
                    result.append(current)
                    
            return result

        def _enforce_min_duration(self, segments: List[Dict]) -> List[Dict]:
            """Ensure segments meet minimum duration by merging with neighbors"""
            if len(segments) <= 1:
                return segments

            result = []
            i = 0
            n = len(segments)
            
            while i < n:
                current = segments[i]
                
                # Skip if segment is long enough or we can't merge further
                if ((current['end_time'] - current['start_time']) >= self.min_segment_duration or 
                    i == 0 or i == n - 1):
                    result.append(current)
                    i += 1
                    continue
                    
                # Try to merge with next segment
                next_seg = segments[i + 1]
                merged = {
                    'start_time': current['start_time'],
                    'end_time': next_seg['end_time'],
                    'text': ' '.join(filter(None, [current.get('text', ''), next_seg.get('text', '')])),
                    'is_silence': current['is_silence'] and next_seg['is_silence']
                }
                
                result.append(merged)
                i += 2  # Skip the next segment as it's been merged
                
            return result

    def generate_transcript_json(self, video_path: str, max_segments: int = 20) -> Dict:
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
        video_duration = result.get('duration', 0)
        
        # Create initial segments from Whisper results
        segments = [
            {
                'start_time': segment['start'],
                'end_time': segment['end'],
                'text': segment['text'].strip(),
                'is_silence': False
            }
            for segment in result['segments']
        ]
        
        # Process segments with SmartSegmentProcessor
        processor = self.SmartSegmentProcessor(
            max_segments=max_segments,
            max_silence_duration=0.3,  # 300ms
            min_segment_duration=0.2    # 200ms
        )
        
        processed_segments = processor.process_segments(segments, video_duration)
        
        # Create project data structure
        video_path = Path(video_path)
        
        # Calculate total duration of all segments
        total_segments_duration = sum(
            seg['end_time'] - seg['start_time'] 
            for seg in processed_segments
        )
        
        project_data = {
            'title': video_path.stem,
            'description': f'Auto-generated from {video_path.name} with smart segment processing',
            'is_public': False,
            'metadata': {
                'video_duration': video_duration,
                'total_segments': len(processed_segments),
                'total_segments_duration': total_segments_duration,
                'processing_timestamp': datetime.datetime.now().isoformat(),
                'processing_notes': 'Processed with SmartSegmentProcessor',
                'segment_stats': {
                    'min_duration': min((s['end_time'] - s['start_time'] for s in processed_segments), default=0),
                    'max_duration': max((s['end_time'] - s['start_time'] for s in processed_segments), default=0),
                    'avg_duration': total_segments_duration / len(processed_segments) if processed_segments else 0,
                    'silent_segments': sum(1 for s in processed_segments if s.get('is_silence', False)),
                    'spoken_segments': sum(1 for s in processed_segments if not s.get('is_silence', True))
                }
            },
            'videos': [
                {
                    'title': video_path.stem,
                    'file_path': str(video_path),
                    'duration': video_duration,
                    'segments': processed_segments,
                    'segment_count': len(processed_segments)
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
