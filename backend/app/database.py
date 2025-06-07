from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
from contextlib import contextmanager

# Create SQLAlchemy engine
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# For SQLite, we need to add check_same_thread=False
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Context manager for database sessions
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# Create all tables
def create_tables():
    from .models.base import Base
    Base.metadata.create_all(bind=engine)

# Initialize database with some test data
def init_db():
    db = SessionLocal()
    try:
        # Create tables if they don't exist
        from .models.base import Base
        Base.metadata.create_all(bind=engine)
        
        # Add any initial data here if needed
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
