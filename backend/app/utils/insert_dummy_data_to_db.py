"""
Database seeding utility for populating the database with initial test data.
"""
from datetime import datetime
from app.database import SessionLocal
from app.models.models import VideoTemplate
from app.schemas import VideoProjectSchema, VideoMetadata, VideoAssetSchema, VideoSegmentSchema, SegmentStats

def seed_video_templates():
    """Seed the database with sample video template data using ORM models."""
    db = SessionLocal()
    
    # Create a VideoProjectSchema object to ensure data validation
    video_project = VideoProjectSchema(
        title="Test Video Project",
        description="This is a test video project",
        is_public=True,
        metadata=VideoMetadata(
            video_duration=120.5,
            total_segments=3,
            total_segments_duration=118.5,
            processing_timestamp=int(datetime.now().timestamp() * 1000),
            processing_notes="Test processing complete",
            segment_stats=SegmentStats(
                min_duration=5.5,
                max_duration=60.0,
                avg_duration=39.5,
                silent_segments=1,
                spoken_segments=2
            ),
            language="en-US"
        ),
        videos=[
            VideoAssetSchema(
                title="Sample Video 1",
                file_path="/videos/sample1.mp4",
                duration=120.5,
                segments=[
                    VideoSegmentSchema(
                        start_time=0.0,
                        end_time=5.5,
                        text="Introduction",
                        is_silence=False
                    ),
                    VideoSegmentSchema(
                        start_time=5.5,
                        end_time=65.5,
                        text="Main content",
                        is_silence=False
                    ),
                    VideoSegmentSchema(
                        start_time=65.5,
                        end_time=120.5,
                        text="Conclusion",
                        is_silence=False
                    )
                ]
            )
        ]
    )

    try:
        # Check if the template already exists
        template_title = "Test Template 1"
        existing_template = db.query(VideoTemplate).filter(VideoTemplate.title == template_title).first()
        
        if not existing_template:
            # Create a new VideoTemplate using the model
            template = VideoTemplate(
                title=template_title,
                description="A test video template with sample data",
                video_project_data=video_project  # This will use our property setter
            )
            
            db.add(template)
            db.commit()
            print("✅ Successfully inserted test data using ORM")
        else:
            print("ℹ️  Database already contains data. No new data was inserted.")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting test data: {e}")
        raise  # Re-raise the exception to see the full traceback
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding database with test data...")
    seed_video_templates()
    print("✨ Done!")
