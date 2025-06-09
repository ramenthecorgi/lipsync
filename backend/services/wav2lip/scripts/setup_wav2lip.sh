#!/bin/bash

# Get the directory of this script
SCRIPT_DIR=$(dirname "$0")

# Create a virtual environment in the wav2lip directory
echo "Creating Python virtual environment for Wav2Lip..."
if [ ! -d "$SCRIPT_DIR/../.venv" ]; then
    python3 -m venv "$SCRIPT_DIR/../.venv"
fi
source "$SCRIPT_DIR/../.venv/bin/activate"


# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip

# Install Wav2Lip requirements
echo "Installing Wav2Lip requirements..."
pip install -r "$SCRIPT_DIR/../requirements_wav2lip.txt"

# Install FFmpeg if not already installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing FFmpeg..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            echo "Homebrew is required to install FFmpeg on macOS"
            echo "Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
        brew install ffmpeg
    else
        # Linux
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    fi
fi

# Clone Wav2Lip repository if it doesn't exist
if [ ! -d "../wav2lip_repo" ]; then
    echo "Cloning Wav2Lip repository..."
    git clone https://github.com/Rudrabha/Wav2Lip.git ../wav2lip_repo
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p ../wav2lip_repo/checkpoints
mkdir -p ../wav2lip_repo/face_detection/detection/sfd

# Download Wav2Lip models
echo "Downloading Wav2Lip models..."
curl -L -# -o ../wav2lip_repo/checkpoints/wav2lip.pth \
    "https://github.com/justinjohn0306/Wav2Lip/releases/download/models/wav2lip.pth"

curl -L -# -o ../wav2lip_repo/checkpoints/wav2lip_gan.pth \
    "https://github.com/justinjohn0306/Wav2Lip/releases/download/models/wav2lip_gan.pth"

# Download face detection model
echo "Downloading face detection model..."
curl -L -# -o ../wav2lip_repo/checkpoints/s3fd-619a316812.pth \
    "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth"

cp ../wav2lip_repo/checkpoints/s3fd-619a316812.pth ../wav2lip_repo/face_detection/detection/sfd/s3fd.pth



echo ""
echo "Wav2Lip setup complete!"
echo "All models have been downloaded and set up."
echo "Activate the virtual environment with: source ../.venv/bin/activate"
