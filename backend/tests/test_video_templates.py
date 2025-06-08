import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models.models import VideoTemplate
from app.schemas import VideoProjectSchema, VideoMetadata, VideoAssetSchema, VideoSegmentSchema, SegmentStats

# Test data
TEST_TEMPLATE_DATA = {
    "title": "Test Template",
    "description": "Test Description",
    "transcription": {
        "title": "Test Project",
        "description": "Test Project Description",
        "is_public": True,
        "metadata": {
            "video_duration": 60.5,
            "total_segments": 2,
            "total_segments_duration": 58.5,
            "processing_timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
            "processing_notes": "Test processing",
            "segment_stats": {
                "min_duration": 1.0,
                "max_duration": 57.5,
                "avg_duration": 29.25,
                "silent_segments": 0,
                "spoken_segments": 2
            },
            "language": "en-US"
        },
        "videos": [
            {
                "title": "Test Video",
                "file_path": "/videos/test.mp4",
                "duration": 60.5,
                "segments": [
                    {
                        "start_time": 1.0,
                        "end_time": 3.0,
                        "text": "First segment",
                        "is_silence": False
                    },
                    {
                        "start_time": 3.0,
                        "end_time": 60.5,
                        "text": "Second segment",
                        "is_silence": False
                    }
                ]
            }
        ]
    }
}

@pytest.fixture
def test_template(db_session: Session) -> VideoTemplate:
    """Create a test video template in the database."""
    # Create a test template
    template = VideoTemplate(
        title=TEST_TEMPLATE_DATA["title"],
        description=TEST_TEMPLATE_DATA["description"],
        transcription=TEST_TEMPLATE_DATA["transcription"]
    )
    
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template

def test_get_template_success(client: TestClient, test_template):
    """Test successfully retrieving a template by ID."""
    # Act
    response = client.get(f"/api/v1/templates/{test_template.id}")
    
    # Assert
    assert response.status_code == 200
    video_project = VideoProjectSchema.model_validate(response.json())

    # now let's validate the VideoMetaData field from video_project
    assert video_project.metadata.video_duration == TEST_TEMPLATE_DATA["transcription"]["metadata"]["video_duration"]
    assert video_project.metadata.total_segments == TEST_TEMPLATE_DATA["transcription"]["metadata"]["total_segments"]
    assert video_project.metadata.total_segments_duration == TEST_TEMPLATE_DATA["transcription"]["metadata"]["total_segments_duration"]
    assert video_project.metadata.processing_timestamp == TEST_TEMPLATE_DATA["transcription"]["metadata"]["processing_timestamp"]
    assert video_project.metadata.processing_notes == TEST_TEMPLATE_DATA["transcription"]["metadata"]["processing_notes"]
    assert video_project.metadata.segment_stats == SegmentStats(
        **TEST_TEMPLATE_DATA["transcription"]["metadata"]["segment_stats"]
    )
    assert video_project.metadata.language == TEST_TEMPLATE_DATA["transcription"]["metadata"]["language"]

def test_get_template_not_found(client: TestClient):
    """Test retrieving a non-existent template returns 404."""
    # Act
    response = client.get("/api/v1/templates/999999")
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Template not found"

def test_get_template_invalid_id(client: TestClient):
    """Test retrieving a template with an invalid ID format returns 400."""
    # Act
    response = client.get("/api/v1/templates/invalid_id")
    
    # Assert
    assert response.status_code == 400
    assert "Invalid template ID format" in response.json()["detail"]

def test_get_template_no_transcription(client: TestClient, db_session: Session):
    """Test retrieving a template with no transcription data returns 400."""
    # Arrange - create a template with no transcription
    template = VideoTemplate(
        title="No Transcription",
        description="Template with no transcription data"
    )
    db_session.add(template)
    db_session.commit()
    
    # Act
    response = client.get(f"/api/v1/templates/{template.id}")
    
    # Assert
    assert response.status_code == 400
    assert "Template has no transcription data" in response.json()["detail"]
