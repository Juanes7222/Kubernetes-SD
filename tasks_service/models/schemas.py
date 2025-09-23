from pydantic import BaseModel
from typing import List, Optional

class CollaboratorIn(BaseModel):
    uid: Optional[str]
    email: Optional[str]

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: Optional[bool] = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    completed: Optional[bool]

class Task(TaskBase):
    id: str
    owner: Optional[dict] = None
    collaborators: Optional[List[dict]] = []