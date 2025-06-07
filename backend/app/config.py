from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Video Editor API"
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Default Vite dev server
        "http://localhost:8000",
    ]
    
    # Database settings (SQLite for development, can be changed to PostgreSQL in production)
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # File storage
    UPLOAD_DIR: str = "uploads"
    STATIC_DIR: str = "static"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # JWT settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create instance
settings = Settings()

# Ensure upload and static directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.STATIC_DIR, exist_ok=True)
