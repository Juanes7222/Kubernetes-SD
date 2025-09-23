from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from core.logging_config import get_logger, write

logger = get_logger(__name__)
router = APIRouter(prefix="/logs", tags=["logs"])

# Simulación de logs en memoria
LOG_STORE: List[Dict[str, Any]] = []

@router.post("", response_model=Dict[str, Any])
def create_log(payload: Dict[str, Any]):
    """Agrega un log al sistema (simulado)"""
    LOG_STORE.append(payload)
    write("info", "create_log", **payload)
    return {"message": "Log registrado correctamente"}

@router.get("", response_model=List[Dict[str, Any]])
def get_logs():
    """Obtiene todos los logs"""
    return LOG_STORE
