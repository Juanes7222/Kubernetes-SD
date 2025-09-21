from pydantic import BaseModel, Field
from typing import Optional, List, Dict
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

class InvitedBy(BaseModel):
    invited_by_uid: str
    invited_by_email: Optional[str] = None
    invited_by_name: Optional[str] = None
    invited_at: str

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
    # owner_id es el UID del creador; se mantiene compatibilidad con `user_id` en DB
    owner_id: str
    # assigned_to es el UID del responsable asignado (puede ser diferente del owner)
    assigned_to: Optional[str] = None
    # Información enriquecida del propietario
    owner: Optional[Owner] = None
    # Información enriquecida del responsable asignado
    assignee: Optional[Owner] = None
    # Lista de colaboradores (objetos con uid, email, display_name)
    collaborators: Optional[List[Collaborator]] = None
    # Información de quién invitó al usuario actual (si es colaborador)
    invited_by: Optional[InvitedBy] = None

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

class AssignTaskRequest(BaseModel):
    # Puede ser UID o email del responsable a asignar
    assignee_uid: Optional[str] = None
    assignee_email: Optional[str] = None