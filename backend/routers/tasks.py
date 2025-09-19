from fastapi import APIRouter, Depends, HTTPException
from core.auth_middleware import get_current_user
from services.firebase_service import firebase_service
from models.schemas import Task, TaskCreate, TaskUpdate, CollaboratorIn
from typing import List, Dict, Any, Optional
from logging_config import get_logger, write

logger = get_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=Task)
def create_task(
    task_input: TaskCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    task_dict = task_input.model_dump()
    created_task = firebase_service.create_task(task_dict, current_user["uid"])
    write("info", "create_task", name=__name__, user=current_user.get("email") or current_user.get("uid"), task_id=created_task.get("id"), title=created_task.get("title"))
    return Task(**created_task)


@router.get("", response_model=List[Task])
def get_tasks(
    search: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    tasks = firebase_service.get_tasks(current_user["uid"], search)
    write("info", "get_tasks", name=__name__, user=current_user.get("email") or current_user.get("uid"), count=len(tasks))
    return [Task(**task) for task in tasks]


@router.get("/{task_id}", response_model=Task)
def get_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    task = firebase_service.get_task_by_id(task_id, current_user["uid"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    write("info", "get_task", name=__name__, user=current_user.get("email") or current_user.get("uid"), task_id=task_id)
    return Task(**task)


@router.put("/{task_id}", response_model=Task)
def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updated_task = firebase_service.update_task(
        task_id,
        current_user["uid"],
        task_update.model_dump(exclude_unset=True)
    )
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    write("info", "update_task", name=__name__, user=current_user.get("email") or current_user.get("uid"), task_id=task_id)
    return Task(**updated_task)


@router.delete("/{task_id}")
def delete_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    success = firebase_service.delete_task(task_id, current_user["uid"])
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    write("info", "delete_task", name=__name__, user=current_user.get("email") or current_user.get("uid"), task_id=task_id)
    return {"message": "Task deleted successfully"}


@router.patch("/{task_id}/toggle", response_model=Task)
def toggle_task_completion(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    toggled_task = firebase_service.toggle_task_completion(task_id, current_user["uid"])
    if not toggled_task:
        raise HTTPException(status_code=404, detail="Task not found")
    write("info", "toggle_task", name=__name__, user=current_user.get("email") or current_user.get("uid"), task_id=task_id, new_completed=toggled_task.get("completed"))
    return Task(**toggled_task)


@router.post("/{task_id}/collaborators", response_model=Task)
def add_collaborator(
    task_id: str,
    payload: CollaboratorIn,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    identifier = payload.email if payload.email else payload.uid
    if not identifier:
        raise HTTPException(status_code=400, detail="Provide email or uid of collaborator")
    updated = firebase_service.add_collaborator(task_id, current_user["uid"], identifier)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found or permission denied")
    write("info", "add_collaborator", name=__name__, user=current_user.get("email") or current_user.get("uid"), task_id=task_id, added=identifier)
    return Task(**updated)


@router.delete("/{task_id}/collaborators/{collab_uid}", response_model=Task)
def remove_collaborator(
    task_id: str,
    collab_uid: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updated = firebase_service.remove_collaborator(task_id, current_user["uid"], collab_uid)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found or permission denied")
    write("info", "remove_collaborator", name=__name__, user=current_user.get("email") or current_user.get("uid"), task_id=task_id, removed=collab_uid)
    return Task(**updated)