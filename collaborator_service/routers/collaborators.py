from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
from services.collaborator_service import collaborator_service
from models.schemas import CollaboratorCreate, CollaboratorResponse
from core.auth_middleware import get_current_user, security
from core.logging_config import write, get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["collaborators"])

@router.post("/{task_id}/collaborators", response_model=CollaboratorResponse)
async def add_collaborator(
    task_id: str,
    collab_data: CollaboratorCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a collaborator to a task"""
    identifier = collab_data.email if collab_data.email else collab_data.uid
    if not identifier:
        raise HTTPException(
            status_code=400,
            detail="Email or UID must be provided"
        )

    # Obtener el token original de las credenciales
    token = credentials.credentials
    
    result = collaborator_service.add_collaborator(
        task_id,
        current_user["uid"],
        identifier,
        token
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Task not found or permission denied"
        )

    write("info", "add_collaborator",
          name=__name__,
          user=current_user["uid"],
          task_id=task_id,
          collaborator=identifier)
    
    return result

@router.delete("/{task_id}/collaborators/{collaborator_id}", response_model=CollaboratorResponse)
async def remove_collaborator(
    task_id: str,
    collaborator_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a collaborator from a task"""
    token = credentials.credentials
    write("info", f"Token received: {token}")
    write("info", f"Removing collaborator {collaborator_id} from task {task_id} by user {current_user['uid']}")
    result = collaborator_service.remove_collaborator(
        task_id,
        current_user["uid"],
        collaborator_id,
        token
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

@router.get("/{task_id}/collaborators", response_model=CollaboratorResponse)
async def get_collaborators(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get collaborators of a task"""
    token = credentials.credentials
    result = collaborator_service.get_collaborators(task_id, current_user["uid"], token)
    
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