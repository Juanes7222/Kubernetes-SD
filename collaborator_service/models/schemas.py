from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class CollaboratorBase(BaseModel):
    """Collaborator base model"""
    email: Optional[EmailStr] = Field(None, description="Colaborador email")
    uid: Optional[str] = Field(None, description="Collaborator UID")

class CollaboratorCreate(CollaboratorBase):
    """Collaborator model for creation"""
    task_id: str = Field(..., description="Task ID")

class Collaborator(CollaboratorBase):
    """Full collaborator model"""
    uid: str
    email: str
    display_name: Optional[str]

class CollaboratorResponse(BaseModel):
    """Response model for collaborator operations"""
    task_id: str
    collaborators: List[Collaborator]