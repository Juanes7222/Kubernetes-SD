from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from services.task_service import task_service
from models.schemas import Task, TaskCreate, TaskUpdate
from core.auth_middleware import get_current_user
from core.logging_config import write, get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=Task)
def create_task(task_input: TaskCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    task_dict = task_input.model_dump()
    created_task = task_service.create_task(task_dict, current_user["uid"])
    write("info", "create_task", 
          name=__name__, 
          user=current_user["uid"],
          task_id=created_task["id"],
          title=created_task.get("title"))
    return Task(**created_task)

@router.get("", response_model=List[Task])
def get_tasks(
    search: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    tasks = task_service.get_tasks(current_user["uid"], search)
    write("info", "get_tasks",
          name=__name__,
          user=current_user["uid"],
          count=len(tasks))
    return [Task(**task) for task in tasks]

@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    task = task_service.get_task_by_id(task_id, current_user["uid"])
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    write("info", "get_task",
          name=__name__,
          user=current_user["uid"],
          task_id=task_id)
    return Task(**task)

@router.put("/{task_id}", response_model=Task)
def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updated_task = task_service.update_task(
        task_id,
        current_user["uid"],
        task_update.model_dump(exclude_unset=True)
    )
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    write("info", "update_task",
          name=__name__,
          user=current_user["uid"],
          task_id=task_id)
    return Task(**updated_task)

@router.delete("/{task_id}")
def delete_task(task_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    success = task_service.delete_task(task_id, current_user["uid"])
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    write("info", "delete_task",
          name=__name__,
          user=current_user["uid"],
          task_id=task_id)
    return {"message": "Task deleted successfully"}

@router.patch("/{task_id}/toggle", response_model=Task)
def toggle_task_completion(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    toggled_task = task_service.toggle_task_completion(task_id, current_user["uid"])
    if not toggled_task:
        raise HTTPException(status_code=404, detail="Task not found")
    write("info", "toggle_task",
          name=__name__,
          user=current_user["uid"],
          task_id=task_id,
          new_completed=toggled_task["completed"])
    return Task(**toggled_task)
