from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os
import uvicorn
from typing import List

from app import models
from app.database import engine, get_db, init_db
from app.config import settings
from app.api.api_v1.api import api_router

# Create necessary directories on startup
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="Video Editor API",
    description="Backend API for the Video Editor application",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc" if settings.ENV != "production" else None,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router, prefix="/api/v1")

# Create necessary directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.STATIC_DIR, exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

# For development - in production, serve the frontend through a proper web server
if settings.ENV == "development":
    from pathlib import Path
    
    # This serves the frontend files in development
    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        frontend_path = Path("../../dist/index.html")  # Adjusted path to find frontend build
        if frontend_path.exists():
            return FileResponse(frontend_path)
        return {"message": "Frontend not built. Run 'npm run build' in the frontend directory."}

# Run the application directly if this file is executed
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
