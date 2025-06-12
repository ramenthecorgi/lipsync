"""Utility functions for audio processing such as concatenation and temporary-file cleanup."""
from pathlib import Path
import subprocess
import uuid
import os
from typing import List

# Base directory for temporary audio (mirrors config in router)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/app/
TEMP_AUDIO_DIR = BASE_DIR / "temp" / "audio"
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def concatenate_audio_ffmpeg(segment_paths: List[str], output_path: str) -> bool:
    """Concatenate multiple WAV files into a single WAV using ffmpeg.

    Args:
        segment_paths: List of WAV file paths to concatenate.
        output_path: Destination WAV path.
    Returns:
        True on success, False otherwise.
    """
    if not segment_paths:
        print("No audio segments provided for concatenation.")
        return False

    list_file_path = TEMP_AUDIO_DIR / f"concat_list_{uuid.uuid4().hex}.txt"
    try:
        with open(list_file_path, "w") as f:
            for path_str in segment_paths:
                abs_path = Path(path_str).resolve()
                f.write(f"file '{abs_path}'\n")

        command = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file_path),
            "-c", "copy",
            str(output_path),
        ]
        print("Running FFmpeg command:", " ".join(command))
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=60)
        if process.returncode != 0:
            print("FFmpeg Error:", stderr.decode())
            return False
        print("Audio concatenated to", output_path)
        return True
    except subprocess.TimeoutExpired:
        print("FFmpeg audio concatenation timed out.")
        if "process" in locals() and process.poll() is None:
            process.kill()
        return False
    except Exception as exc:
        print("Error running FFmpeg:", exc)
        return False
    finally:
        if list_file_path.exists():
            try:
                list_file_path.unlink()
            except Exception as unlink_err:
                print(f"Error deleting concat list file {list_file_path}: {unlink_err}")


def cleanup_temp_audio(audio_path: str):
    """Delete a temporary audio file if it exists."""
    try:
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)
            print("Cleaned up temporary audio file:", audio_path)
    except Exception as exc:
        print(f"Error cleaning up audio file {audio_path}: {exc}")
