from fastapi import APIRouter

from app.api.routers import auth, video_templates, lip_sync

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(video_templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(lip_sync.router, prefix="/lip-sync", tags=["lip-sync"])
