from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, date
import uuid

# Define Models
class User(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    email_verified: bool = False

class CollaboratorIn(BaseModel):
    # Permitir enviar uid o email para identificar al colaborador
    uid: Optional[str] = None
    email: Optional[str] = None


class Collaborator(BaseModel):
    uid: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None

class Owner(BaseModel):
    uid: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    due_date: Optional[date] = None
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    owner_id: str
    collaborators: Optional[List[Collaborator]] = None
    
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    due_date: Optional[date] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    completed: Optional[bool] = None
    assigned_to: Optional[str] = None
