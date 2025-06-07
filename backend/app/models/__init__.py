# This file makes the models directory a Python package
from .base import Base, BaseModel
from .models import User, Project, Video, VideoSegment

# Make models available at the package level
__all__ = [
    'Base',
    'BaseModel',
    'User',
    'Project',
    'Video',
    'VideoSegment',
]
