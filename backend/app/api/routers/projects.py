from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ... import schemas, models
from ...database import get_db
from ...core.security import get_current_active_user

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=schemas.Project)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Create a new project."""
    db_project = models.Project(
        **project.dict(),
        owner_id=current_user.id
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project

@router.get("/", response_model=List[schemas.Project])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    is_public: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """List all projects for the current user."""
    query = db.query(models.Project).filter(
        models.Project.owner_id == current_user.id
    )
    
    # Apply filters if provided
    if is_public is not None:
        query = query.filter(models.Project.is_public == is_public)
    
    projects = query.offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}", response_model=schemas.Project)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get a specific project by ID."""
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied")
        
    return project

@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int,
    project_update: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Update a project."""
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied")
    
    # Update project fields
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Delete a project and all its videos."""
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied")
    
    # Note: Videos and segments will be deleted due to CASCADE in the database
    db.delete(project)
    db.commit()
    
    return None
