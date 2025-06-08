import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import VideoTemplate
from app.schemas import VideoProjectSchema, VideoAssetSchema, VideoSegmentSchema, VideoMetadata, SegmentStats

def create_test_video_project_schema() -> VideoProjectSchema:
    """Helper function to create a test VideoProjectSchema."""
    return VideoProjectSchema(
        title="Test Video",
        description="A test video project",
        is_public=True,
        metadata=VideoMetadata(
            video_duration=10.5,
            total_segments=3,
            total_segments_duration=9.5,
            processing_timestamp=int(datetime.now().timestamp() * 1000),  # Convert to milliseconds
            processing_notes="Test processing",
            segment_stats=SegmentStats(
                min_duration=1.0,
                max_duration=5.0,
                avg_duration=3.17,
                silent_segments=1,
                spoken_segments=2
            )
        ),
        videos=[
            VideoAssetSchema(
                title="Test Video Asset",
                file_path="/path/to/video.mp4",
                duration=10.5,
                segments=[
                    VideoSegmentSchema(
                        start_time=0.0,
                        end_time=2.5,
                        text="First segment",
                        is_silence=False
                    ),
                    VideoSegmentSchema(
                        start_time=2.5,
                        end_time=7.5,
                        text="Second segment",
                        is_silence=False
                    )
                ]
            )
        ]
    )

class TestVideoTemplate:
    def test_create_video_template(self, db_session: Session):
        """Test creating a basic VideoTemplate."""
        template = VideoTemplate(
            title="Test Template",
            description="A test template"
        )
        db_session.add(template)
        db_session.commit()
        
        assert template.id is not None
        assert template.title == "Test Template"
        assert template.description == "A test template"
        assert template.transcription is None
        assert template.transcription_data is None

    def test_transcription_data_property(self, db_session: Session):
        """Test the transcription_data property."""
        # Create a test schema
        schema = create_test_video_project_schema()
        
        # Create template with transcription
        template = VideoTemplate(
            title="Test Template",
            transcription=schema.model_dump()
        )
        db_session.add(template)
        db_session.commit()
        
        # Test getting transcription data
        retrieved = template.transcription_data
        assert isinstance(retrieved, VideoProjectSchema)
        assert retrieved.title == "Test Video"
        assert len(retrieved.videos) == 1
        assert retrieved.videos[0].title == "Test Video Asset"

    def test_transcription_data_setter(self, db_session: Session):
        """Test setting transcription_data with a VideoProjectSchema."""
        schema = create_test_video_project_schema()
        
        template = VideoTemplate(title="Test Template")
        template.transcription_data = schema
        
        assert template.transcription is not None
        assert isinstance(template.transcription, dict)
        assert template.transcription["title"] == "Test Video"
        
        # Test that the data can be retrieved back as a schema
        retrieved = template.transcription_data
        assert isinstance(retrieved, VideoProjectSchema)
        assert retrieved.title == "Test Video"

    def test_update_from_schema(self, db_session: Session):
        """Test updating a template from a VideoProjectSchema."""
        schema = create_test_video_project_schema()
        
        template = VideoTemplate(title="Old Title")
        template.update_from_schema(schema)
        
        assert template.title == "Test Video"
        assert template.description == "A test video project"
        assert template.transcription is not None
        
        # Verify the transcription data was set correctly
        assert template.transcription_data is not None
        assert template.transcription_data.title == "Test Video"

    def test_invalid_transcription_data(self, db_session: Session):
        """Test that invalid transcription data raises validation errors."""
        template = VideoTemplate(title="Test Template")
        
        # Test with invalid data (missing required fields)
        with pytest.raises(ValueError):
            # This will fail validation when we try to access transcription_data
            template.transcription = {"invalid": "data"}
            # Accessing the property will trigger validation
            _ = template.transcription_data
            
    def test_null_transcription(self, db_session: Session):
        """Test that None transcription is handled correctly."""
        template = VideoTemplate(title="Test Template", transcription=None)
        db_session.add(template)
        db_session.commit()
        
        assert template.transcription is None
        assert template.transcription_data is None
        
        # Test setting to None
        template.transcription_data = None
        assert template.transcription is None
        assert template.transcription_data is None
