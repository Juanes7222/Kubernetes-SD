import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any

# SOLO el logs_service tiene carpeta logs
LOG_DIR = Path(__file__).parent / "../logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "logs_service") -> logging.Logger:
    """Only logs_service has file handler, others not use it"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (rotating) - SOLO aquí se escriben archivos
    fh = RotatingFileHandler(
        LOG_DIR / "centralized.log", 
        maxBytes=10 * 1024 * 1024, 
        backupCount=5, 
        encoding='utf-8'
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def write(level: str, message: str, name: Optional[str] = None, **meta: Any) -> None:
    """General logging function"""
    logger = get_logger(name or "logs_service")
    
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

def client_log(level: str, message: str, user: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> None:
    """Log events from clients/services"""
    meta = meta or {}
    if user is not None:
        meta['user'] = user
    write(level, message, name="client", **meta)

def request_log(method: str, path: str, status: int, time: float, auth: bool = False, name: Optional[str] = None) -> None:
    """Log HTTP requests"""
    write("info", f"request {method} {path} status={status} time={time:.3f}s auth={auth}", name=name or "request")