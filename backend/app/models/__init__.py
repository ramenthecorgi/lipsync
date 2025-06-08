# This file makes the models directory a Python package
from .base import Base, BaseModel
from .models import User, Project, VideoTemplate

# Make models available at the package level
__all__ = [
    'Base',
    'BaseModel',
    'User',
    'Project',
    'VideoTemplate',
]
