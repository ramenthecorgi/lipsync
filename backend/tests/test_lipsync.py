import os
import requests
from pathlib import Path
from test_utils import TestMediaGenerator

# Configuration
BASE_URL = "http://localhost:8000/api/v1/videos"
OUTPUT_DIR = "output_videos"

def test_lipsync_endpoint():
    # Setup test files
    print("Setting up test environment...")
    generator = TestMediaGenerator()
    
    # Create test files (3 seconds each) - will reuse existing files if they exist
    print("\nGetting or creating test video...")
    video_path = generator.create_test_video(duration=3)
    
    print("\nGetting or creating test audio...")
    audio_path = generator.create_test_audio(duration=3)
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "test_output.mp4")
    
    # Test data
    test_data = {
        "video_path": video_path,
        "audio_path": audio_path,
        "output_path": output_path
    }
    
    print("\nTesting lip-sync endpoint with:")
    print(f"Video: {video_path}")
    print(f"Audio: {audio_path}")
    print(f"Output: {output_path}")
    
    try:
        # Make the request
        print("\nSending request to lip-sync endpoint...")
        response = requests.post(
            f"{BASE_URL}/generate-lipsync",
            json=test_data,
            timeout=60  # 60 seconds timeout
        )
        
        # Print results
        print(f"\nStatus Code: {response.status_code}")
        try:
            print("Response:", response.json())
        except ValueError:
            print("Response Text:", response.text)
                
        if response.status_code == 200:
            print(f"\n✅ Success! Output video should be at: {output_path}")
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"File size: {size_mb:.2f} MB")
                print("✅ Test passed!")
                return True
            else:
                print("❌ Test failed: Output file was not created")
        else:
            print(f"❌ Test failed with status code: {response.status_code}")
        
        return False
    
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_lipsync_endpoint()
