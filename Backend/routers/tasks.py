from fastapi import APIRouter, Depends
from core.authentication import verify_token
from models.schemas import Task
from services.tasks import TaskServices

router = APIRouter(prefix="/lists/{list_id}/tasks",
                   tags=["Tareas"])

@router.post("/", response_model=Task)
def create_task(list_id: str, task: Task, uid: str = Depends(verify_token)):
    return TaskServices.create_task(list_id, task, uid)