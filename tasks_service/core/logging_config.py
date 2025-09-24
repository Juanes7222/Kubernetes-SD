import logging
import os
from datetime import datetime
import requests
from typing import Any, Dict, Optional
from core import config

# URL del servicio de logs
LOGS_SERVICE_URL = config.LOGS_SERVICE_URL

def get_logger(name: str) -> logging.Logger:
    """Logger config with console handler and sending to log service"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        # Solo handler de consola para desarrollo local
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(config.LOG_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # No propagar a otros loggers
        logger.propagate = False
    
    return logger

def format_log_data(action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Data log format for sending to centralized service"""
    meta = {
        "service": config.SERVICE_NAME,
        "logger_name": __name__,
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }
    return meta

def send_to_log_service(level: str, message: str, user: Optional[str] = None, meta: Dict[str, Any] = None) -> None:
    """Send log to centralized service"""
    try:
        payload = {
            "level": level,
            "message": message,
            "user": user,
            "meta": meta or {}
        }
        requests.post(LOGS_SERVICE_URL, json=payload, timeout=1)
    except Exception as e:
        # Si falla el envío al servicio de logs, al menos logueamos localmente
        logger = get_logger(__name__)
        logger.error(f"Error sending log to logs service: {e}")

def write(level: str, action: str, **kwargs: Any) -> None:
    """Write structured log and send it to centralized service"""
    meta = format_log_data(action, kwargs)
    user = kwargs.get("user")
    message = f"{action}: " + " ".join(f"{k}={v}" for k, v in kwargs.items() if k != "user")
    
    # Enviar al servicio de logs
    send_to_log_service(level, message, user=user, meta=meta)
    
    # También mantener log local para desarrollo/debug
    logger = get_logger(__name__)
    level_method = getattr(logger, level.lower(), logger.info)
    level_method(message)