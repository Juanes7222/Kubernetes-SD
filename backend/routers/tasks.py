from fastapi import APIRouter, Depends, HTTPException
from core.auth_middleware import get_current_user
from services.firebase_service import firebase_service
from models.schemas import Task, TaskCreate, TaskUpdate
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=Task)
def create_task(
    task_input: TaskCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    task_dict = task_input.model_dump()
    created_task = firebase_service.create_task(task_dict, current_user["uid"])
    return Task(**created_task)


@router.get("", response_model=List[Task])
def get_tasks(
    search: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    tasks = firebase_service.get_tasks(current_user["uid"], search)
    return [Task(**task) for task in tasks]


@router.get("/{task_id}", response_model=Task)
def get_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    task = firebase_service.get_task_by_id(task_id, current_user["uid"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
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
    return Task(**updated_task)


@router.delete("/{task_id}")
def delete_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    success = firebase_service.delete_task(task_id, current_user["uid"])
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}


@router.patch("/{task_id}/toggle", response_model=Task)
def toggle_task_completion(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    toggled_task = firebase_service.toggle_task_completion(task_id, current_user["uid"])
    if not toggled_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return Task(**toggled_task)