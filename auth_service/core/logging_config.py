import logging
from typing import Optional, Any
import httpx
from core.config import settings

# NO hay carpeta logs aquí - solo envío al servicio centralizado

def get_logger(name: str = "auth_service") -> logging.Logger:
    """Logger mínimo solo para errores críticos del servicio"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.ERROR)  # Solo errores críticos
    
    # Solo console handler para errores del servicio mismo
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

async def send_log_to_service(level: str, message: str, name: Optional[str] = None, **meta: Any) -> None:
    """Envía TODOS los logs al servicio centralizado"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "level": level,
                "message": message,
                "meta": {**meta, "service": "auth", "logger_name": name or "auth_service"}
            }
            # Agregar user si está en meta
            if 'user' in meta:
                payload["user"] = meta['user']
                
            await client.post(
                f"{settings.LOGS_SERVICE_URL}/api/logs/client",
                json=payload,
                timeout=5.0
            )
    except Exception as e:
        # Fallback: solo log local para errores de conexión al logs_service
        logger = get_logger("logging_fallback")
        logger.error(f"Failed to send log to service: {e} - Original: {message}")

def write(level: str, message: str, name: Optional[str] = None, **meta: Any) -> None:
    """Envía log al servicio centralizado"""
    # Enviar asincrónicamente al servicio de logs
    import asyncio
    asyncio.create_task(send_log_to_service(level, message, name, **meta))

def request_log(method: str, path: str, status: int, time: float, auth: bool = False, name: Optional[str] = None) -> None:
    """Log HTTP requests - enviado al servicio centralizado"""
    write("info", f"request {method} {path} status={status} time={time:.3f}s auth={auth}", 
          name=name or "auth_request")