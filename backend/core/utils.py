from logging_config import get_logger
from fastapi import HTTPException
from datetime import datetime, date

logger = get_logger(__name__)

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
    
def get_path_credentials():
    """
    Obtiene la ruta a las credenciales de Firebase desde la variable de entorno
    FIREBASE_CREDENTIALS o usa una ruta por defecto.
    """
    from pathlib import Path
    import os

    cred_path = os.getenv("FIREBASE_CREDENTIALS", None)
    
    if not cred_path:
        cred_path = Path(__file__).parent.parent / 'secrets/kubernetes-sd.json'
    return cred_path