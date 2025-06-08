"""
Database initialization script.
Run this script to create all database tables defined in the models.
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from app.database import engine
from app.models.base import Base
from app.models.models import *  # Import all models to register them with Base.metadata

def create_tables():
    """Create all database tables defined in the models."""
    print("Creating database tables...")
    try:
        # This will create all tables that don't already exist
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    create_tables()
