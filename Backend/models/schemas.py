from pydantic import BaseModel
from typing import List, Optional


class Task(BaseModel):
    id_task: Optional[str]
    title: str
    description: str
    completed: bool = False

class TaskList(BaseModel):
    id: Optional[str]
    name: str
    tasks: List[Task] = []