import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from core.config import settings

LOG_DIR = Path(__file__).parent / "../logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "auth_service") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fh = RotatingFileHandler(LOG_DIR / "auth_service.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

async def send_log_to_service(level: str, message: str, name: Optional[str] = None, **meta: Any) -> None:
    """Send log to logs service"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.LOGS_SERVICE_URL}/api/logs/client",
                json={
                    "level": level,
                    "message": message,
                    "meta": {**meta, "service": "auth", "logger_name": name}
                },
                timeout=5.0
            )
    except Exception as e:
        # Fallback to local logging if service is unavailable
        logger = get_logger("logging_fallback")
        if level == "error":
            logger.error(f"Failed to send log to service: {e} - {message}")

def write(level: str, message: str, name: Optional[str] = None, **meta: Any) -> None:
    """Unified write helper that sends to logs service"""
    logger = get_logger(name or "auth_service")
    
    if meta:
        meta_str = " " + " ".join(f"{k}={v}" for k, v in meta.items())
    else:
        meta_str = ""

    msg = f"{message}{meta_str}"
    lvl = level.lower()

    if lvl == "debug":
        logger.debug(msg)
    elif lvl in ("warning", "warn"):
        logger.warning(msg)
    elif lvl == "error":
        logger.error(msg)
    else:
        logger.info(msg)
    
    # Also send to logs service
    import asyncio
    asyncio.create_task(send_log_to_service(level, message, name, **meta))

def request_log(method: str, path: str, status: int, time: float, auth: bool = False, name: Optional[str] = None) -> None:
    """Log HTTP requests"""
    write("info", f"request {method} {path} status={status} time={time:.3f}s auth={auth}", name=name or "auth_request")