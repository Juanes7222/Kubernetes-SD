from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone, date
import uuid

# Define Models
class User(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    email_verified: bool = False

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    due_date: Optional[date] = None
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    due_date: Optional[date] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    completed: Optional[bool] = None