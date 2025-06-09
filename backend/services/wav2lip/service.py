import os
import sys
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Wav2LipService:
    def __init__(self, wav2lip_root: str = None, venv_path: str = None):
        """
        Initialize Wav2Lip service.
        
        Args:
            wav2lip_root: Path to the Wav2Lip repository root
            venv_path: Path to the virtual environment with Wav2Lip dependencies
        """
        # Set up logging
        logger.setLevel(logging.DEBUG)
        
        # Set up Wav2Lip root
        self.wav2lip_root = str(wav2lip_root) if wav2lip_root else str(
            Path(__file__).parent.parent / "wav2lip_repo"
        )
        logger.info(f"Wav2Lip repository path: {self.wav2lip_root}")
        
        # Set up virtual environment paths
        self.venv_path = str(venv_path) if venv_path else str(
            Path(__file__).parent.parent / ".venv"
        )
        
        # Verify paths exist
        if not Path(self.wav2lip_root).exists():
            logger.warning(f"Wav2Lip repository not found at {self.wav2lip_root}")
        if not Path(self.venv_path).exists():
            logger.warning(f"Virtual environment not found at {self.venv_path}")
            
        # Verify Python executable exists in venv
        python_path = Path(self.venv_path) / "bin" / "python"
        if not python_path.exists():
            logger.warning(f"Python executable not found in virtual environment")
        logger.info(f"Using virtual environment at: {self.venv_path}")
        
        # Determine Python executable based on platform
        if os.name == 'nt':  # Windows
            self.python_exec = os.path.join(self.venv_path, 'Scripts', 'python.exe')
        else:  # Unix/Linux/MacOS
            self.python_exec = os.path.join(self.venv_path, 'bin', 'python')
        logger.info(f"Using Python executable: {self.python_exec}")
        
            
        # Default model paths
        self.checkpoint_path = os.path.join(self.wav2lip_root, "checkpoints", "wav2lip.pth")
        # Use this for higher quality but slower results
        # self.checkpoint_path = os.path.join(self.wav2lip_root, "checkpoints", "wav2lip_gan.pth")
        self.face_detector_path = os.path.join(
            self.wav2lip_root, "face_detection", "detection", "sfd", "s3fd.pth"
        )
        
        # Verify paths
        self._verify_paths()
        
        logger.info("Wav2LipService initialized successfully")
    
    def _verify_paths(self):
        """Verify that all required files and directories exist."""
        required_paths = [
            (self.wav2lip_root, "Wav2Lip repository"),
            (self.checkpoint_path, "Wav2Lip model"),
            (self.face_detector_path, "Face detection model"),
            (self.venv_path, "Virtual environment"),
            (self.python_exec, "Python executable")
        ]
        
        for path, name in required_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"{name} not found at {path}")
    
    def _run_wav2lip_subprocess(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        **kwargs
    ) -> str:
        """Run Wav2Lip in a subprocess using the virtual environment."""
        # Prepare the command
        cmd = [
            self.python_exec,
            os.path.join(self.wav2lip_root, "inference.py"),
            "--checkpoint_path", self.checkpoint_path,
            "--face", video_path,
            "--audio", audio_path,
            "--outfile", output_path,
            "--face_det_batch_size", str(kwargs.get("face_det_batch_size", 1)),
            "--wav2lip_batch_size", str(kwargs.get("wav2lip_batch_size", 16)),
            "--resize_factor", str(kwargs.get("resize_factor", 1)),
            "--fps", str(kwargs.get("fps", 25.0)),
            "--pads", *map(str, kwargs.get("pads", [0, 10, 0, 0]))
        ]
        
        # Add optional arguments
        if kwargs.get("static", False):
            cmd.append("--static")
        if kwargs.get("nosmooth", False):
            cmd.append("--nosmooth")
        if kwargs.get("rotate", False):
            cmd.append("--rotate")
        if "crop" in kwargs and kwargs["crop"]:
            cmd.extend(["--crop"] + list(map(str, kwargs["crop"])))
        
        # Run the command
        try:
            # Debug information
            logger.info(f"Using Python executable: {self.python_exec}")
            logger.info(f"Python path: {os.environ.get('PYTHONPATH', 'Not set')}")
            
            # Add a debug command to check librosa version in the subprocess
            debug_cmd = [
                self.python_exec,
                '-c',
                'import librosa; print(f"Librosa version: {librosa.__version__}"); print(f"Librosa path: {librosa.__file__}")'
            ]
            
            logger.info("Running debug command to check librosa:")
            debug_result = subprocess.run(
                debug_cmd,
                cwd=self.wav2lip_root,
                capture_output=True,
                text=True
            )
            logger.info(f"Debug output: {debug_result.stdout}")
            if debug_result.stderr:
                logger.error(f"Debug error: {debug_result.stderr}")
                
            logger.info(f"Running Wav2Lip command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.wav2lip_root,
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Wav2Lip output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Wav2Lip warnings: {result.stderr}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Wav2Lip failed with error: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def generate_lipsync(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        **kwargs
    ) -> str:
        """
        Generate a lip-synced video using Wav2Lip.
        
        Args:
            video_path: Path to the input video file
            audio_path: Path to the input audio file
            output_path: Path where the output video will be saved
            **kwargs: Additional Wav2Lip parameters
                - face_det_batch_size: Batch size for face detection
                - wav2lip_batch_size: Batch size for Wav2Lip
                - resize_factor: Resize factor for processing
                - fps: Frames per second of output video
                - pads: Padding for the face [top, bottom, left, right]
                - static: Whether to use static images
                - nosmooth: Disable smoothing of face detections
                - rotate: Rotate the video if face is not detected
                - crop: Crop the video [x1, y1, x2, y2]
                
        Returns:
            str: Path to the generated output video
            
        Raises:
            RuntimeError: If Wav2Lip processing fails
            FileNotFoundError: If input files are not found
        """
        # Verify input files exist
        for path, name in [
            (video_path, "Input video"),
            (audio_path, "Input audio"),
            (os.path.dirname(output_path), "Output directory")
        ]:
            if not os.path.exists(path) and path != os.path.dirname(output_path):
                raise FileNotFoundError(f"{name} not found at {path}")
                
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        logger.info(f"Starting Wav2Lip processing for {video_path} with audio {audio_path}")
        logger.info(f"Output will be saved to {output_path}")
        
        try:
            return self._run_wav2lip_subprocess(
                video_path=video_path,
                audio_path=audio_path,
                output_path=output_path,
                **kwargs  # Pass all additional parameters through
            )
        except Exception as e:
            logger.error(f"Error in Wav2Lip processing: {str(e)}", exc_info=True)
            raise
