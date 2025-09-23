from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class TaskBase(BaseModel):
    """Base model for tasks"""
    title: str = Field(..., description="Título de la tarea")
    description: Optional[str] = Field(None, description="Descripción detallada de la tarea")
    completed: bool = Field(False, description="Estado de completado de la tarea")

class TaskCreate(TaskBase):
    """Create a new task model"""
    pass

class TaskUpdate(BaseModel):
    """Task update model"""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Task(TaskBase):
    """Task full model"""
    id: str = Field(..., description="Identificador único de la tarea")
    owner_id: str = Field(..., description="ID del usuario propietario")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")