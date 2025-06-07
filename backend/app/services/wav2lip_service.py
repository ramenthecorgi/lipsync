import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class Wav2LipService:
    def __init__(self, wav2lip_root: str = None):
        """
        Initialize Wav2Lip service.
        
        Args:
            wav2lip_root: Path to the Wav2Lip repository root
        """
        if wav2lip_root is None:
            self.wav2lip_root = str(Path(__file__).parent.parent.parent / "wav2lip_repo")
        else:
            self.wav2lip_root = wav2lip_root
            
        # Add Wav2Lip to Python path
        sys.path.insert(0, self.wav2lip_root)
        
        # Default model paths
        self.checkpoint_path = os.path.join(self.wav2lip_root, "checkpoints", "wav2lip_gan.pth")
        self.face_detector_path = os.path.join(
            self.wav2lip_root, "face_detection", "detection", "sfd", "s3fd.pth"
        )
        
        # Verify paths
        self._verify_paths()
    
    def _verify_paths(self):
        """Verify that all required files exist."""
        required_paths = [
            (self.checkpoint_path, "Wav2Lip model"),
            (self.face_detector_path, "Face detection model"),
        ]
        
        for path, name in required_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"{name} not found at {path}")
    
    def generate_lipsync(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        face_det_batch_size: int = 1,
        wav2lip_batch_size: int = 16,
        resize_factor: int = 1,
        crop: Tuple[int, int, int, int] = None,
        rotate: bool = False,
        nosmooth: bool = False,
        fps: float = 25.0,
        pads: Tuple[int, int, int, int] = (0, 10, 0, 0),
        face_detector: str = "sfd",
        static: bool = False,
    ) -> str:
        """
        Generate lip-synced video using Wav2Lip.
        
        Args:
            video_path: Path to the input video file
            audio_path: Path to the input audio file
            output_path: Path to save the output video
            face_det_batch_size: Batch size for face detection
            wav2lip_batch_size: Batch size for Wav2Lip
            resize_factor: Reduce the resolution by this factor
            crop: Crop video (top, bottom, left, right)
            rotate: Rotate video 90 degrees counter-clockwise
            nosmooth: Disable smoothing of face detections
            fps: FPS of output video
            pads: Padding (top, bottom, left, right) for face detection
            face_detector: Face detector to use (sfd or retinaface)
            static: Use first frame for all frames (for static images)
            
        Returns:
            Path to the generated video file
        """
        try:
            # Prepare command
            cmd = [
                sys.executable,  # Use the same Python interpreter
                os.path.join(self.wav2lip_root, "inference.py"),
                "--checkpoint_path", self.checkpoint_path,
                "--face", video_path,
                "--audio", audio_path,
                "--outfile", output_path,
                "--face_det_batch_size", str(face_det_batch_size),
                "--wav2lip_batch_size", str(wav2lip_batch_size),
                "--resize_factor", str(resize_factor),
                "--fps", str(fps),
                "--pads", *map(str, pads),
            ]
            
            # Add optional arguments
            if static:
                cmd.append("--static")
            if nosmooth:
                cmd.append("--nosmooth")
            if crop:
                cmd.extend(["--crop"] + list(map(str, crop)))
            if rotate:
                cmd.append("--rotate")
            
            logger.info(f"Running Wav2Lip command: {' '.join(cmd)}")
            
            # Run the command
            result = subprocess.run(
                cmd,
                cwd=self.wav2lip_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                error_msg = f"Wav2Lip failed with error: {result.stderr}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            if not os.path.exists(output_path):
                raise RuntimeError(f"Wav2Lip did not create output file at {output_path}")
                
            logger.info(f"Successfully generated lip-synced video at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in Wav2Lip generation: {str(e)}", exc_info=True)
            raise
