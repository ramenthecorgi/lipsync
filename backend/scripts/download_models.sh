#!/bin/bash
set -e  # Exit on error

# Create directories
mkdir -p wav2lip_repo/checkpoints
mkdir -p wav2lip_repo/face_detection/detection/sfd

# Download Wav2Lip models
echo "Downloading Wav2Lip models..."
curl -L -# -o wav2lip_repo/checkpoints/wav2lip.pth \
    "https://github.com/justinjohn0306/Wav2Lip/releases/download/models/wav2lip.pth"

curl -L -# -o wav2lip_repo/checkpoints/wav2lip_gan.pth \
    "https://github.com/justinjohn0306/Wav2Lip/releases/download/models/wav2lip_gan.pth"

# Download face detection model
echo "Downloading face detection model..."
curl -L -# -o wav2lip_repo/checkpoints/s3fd-619a316812.pth \
    "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth"

# Copy face detection model to the correct location
cp wav2lip_repo/checkpoints/s3fd-619a316812.pth wav2lip_repo/face_detection/detection/sfd/s3fd.pth

echo "✅ All models downloaded successfully!"
echo "Models are located in:"
echo "- $(pwd)/wav2lip_repo/checkpoints/"
echo "- $(pwd)/wav2lip_repo/face_detection/detection/sfd/"
