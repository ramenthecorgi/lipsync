import os
import sys
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.base import Base
from app.models.models import VideoTemplate
from app.schemas import VideoProjectSchema, VideoAssetSchema, VideoSegmentSchema, VideoMetadata, SegmentStats

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

db_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=db_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=db_engine)
