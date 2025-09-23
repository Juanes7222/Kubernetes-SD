from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from services.collaborator_service import collaborator_service
from models.schemas import CollaboratorCreate, CollaboratorResponse
from core.auth_middleware import get_current_user
from core.logging_config import write, get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/collaborators", tags=["collaborators"])

@router.post("", response_model=CollaboratorResponse)
async def add_collaborator(
    collab_data: CollaboratorCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a collaborator to a task"""
    identifier = collab_data.email if collab_data.email else collab_data.uid
    if not identifier:
        raise HTTPException(
            status_code=400,
            detail="Email or UID must be provided"
        )

    result = collaborator_service.add_collaborator(
        collab_data.task_id,
        current_user["uid"],
        identifier
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Task not found or permission denied"
        )

    write("info", "add_collaborator",
          name=__name__,
          user=current_user["uid"],
          task_id=collab_data.task_id,
          collaborator=identifier)
    
    return result

@router.delete("/{task_id}/{collaborator_id}", response_model=CollaboratorResponse)
async def remove_collaborator(
    task_id: str,
    collaborator_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a collaborator from a task"""
    result = collaborator_service.remove_collaborator(
        task_id,
        current_user["uid"],
        collaborator_id
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Task not found or permission denied"
        )

    write("info", "remove_collaborator",
          name=__name__,
          user=current_user["uid"],
          task_id=task_id,
          collaborator=collaborator_id)
    
    return result

@router.get("/{task_id}", response_model=CollaboratorResponse)
async def get_collaborators(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get collaborators of a task"""
    result = collaborator_service.get_collaborators(task_id, current_user["uid"])
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Task not found or permission denied"
        )

    write("info", "get_collaborators",
          name=__name__,
          user=current_user["uid"],
          task_id=task_id)
    
    return result