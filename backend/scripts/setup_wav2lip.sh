#!/bin/bash

# Create a virtual environment
echo "Creating Python virtual environment..."
python3 -m venv wav2lip-venv
source wav2lip-venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip

# Install PyTorch with CUDA 11.8
echo "Installing PyTorch with CUDA 11.8..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install Wav2Lip requirements
echo "Installing Wav2Lip requirements..."
pip install -r ../requirements_wav2lip.txt

# Install additional requirements for Wav2Lip
echo "Installing additional requirements..."
pip install imageio imageio-ffmpeg pillow python-dotenv

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
    
    # Download face detection model
    echo "Downloading face detection model..."
    mkdir -p ../wav2lip_repo/face_detection/detection/sfd
    wget 'https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth' -O ../wav2lip_repo/face_detection/detection/sfd/s3fd.pth
fi

echo ""
echo "Wav2Lip setup complete!"
echo "Activate the virtual environment with: source wav2lip-venv/bin/activate"
echo "You may need to download the Wav2Lip models manually if they weren't downloaded automatically."
