import logging
from fastapi import HTTPException
from datetime import datetime, date

logger = logging.getLogger(__name__)

def to_firestore_dates(data: dict) -> dict:
    """
    Convierte objetos date en ISO strings para Firestore.
    Modifica y devuelve el dict.
    """
    if not data:
        return data
    if data.get("due_date") and isinstance(data["due_date"], date):
        data["due_date"] = data["due_date"].isoformat()
    return data

def from_firestore_dates(data: dict) -> dict:
    """
    Convierte cadenas ISO en date (si aplica). No falla si el formato es inesperado.
    """
    if not data:
        return data
    if data.get("due_date"):
        try:
            data["due_date"] = datetime.fromisoformat(data["due_date"]).date()
        except Exception:
            logger.debug("No se pudo parsear due_date: %s", data.get("due_date"))
            data["due_date"] = None
    return data

async def safe_firebase_call(coro, *args, **kwargs):
    """
    Ejecuta la llamada a firebase_service de forma segura:
    - Deja pasar HTTPException.
    - Para cualquier otra excepción se registra y se lanza HTTP 500.
    """
    try:
        result = coro(*args, **kwargs)
        if hasattr(result, "__await__"):  # si es async
            return await result
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en llamada a Firebase: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")