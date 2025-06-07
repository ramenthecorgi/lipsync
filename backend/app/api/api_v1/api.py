from fastapi import APIRouter

from app.api.routers import auth, projects, videos

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
