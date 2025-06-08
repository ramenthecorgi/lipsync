import os
import sys
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import models to ensure they are registered with SQLAlchemy
from app.models.base import Base
from app.models.models import VideoTemplate, User, Project
from app.database import engine as prod_engine, SessionLocal as ProdSessionLocal, get_db

# Import all models to ensure they are registered with SQLAlchemy
from app import models  # noqa: F401

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine and session factory
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True  # Enable SQL logging for tests
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Store original engine and session
original_engine = prod_engine
original_session = ProdSessionLocal

# Override the database engine with test engine
from app import database as db_module
from app.database import engine as db_engine

db_engine._engine = test_engine  # type: ignore
db_module.engine = test_engine

# Update the session factory to use our test engine
db_module.SessionLocal = TestingSessionLocal

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Import here to avoid circular imports
    from app.models.base import Base
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        # Clean up tables
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client(db_session: Session):
    """Create a test client that uses the `db_session` fixture for database access."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db
    
    # Override the get_db dependency to use our test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close the session here, it's handled by the fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()

# Clean up after all tests
def pytest_sessionfinish(session, exitstatus):
    # Restore original engine
    test_engine.dispose()
    global prod_engine
    prod_engine = original_engine
