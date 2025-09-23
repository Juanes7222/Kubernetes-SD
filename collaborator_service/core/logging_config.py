import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from core import config

# Crear el directorio de logs si no existe
log_dir = Path(config.BASE_DIR) / "logs"
log_dir.mkdir(exist_ok=True)

# Configurar el formato del logger
formatter = logging.Formatter(config.LOG_FORMAT)

def setup_logger(name: str) -> logging.Logger:
    """Configurar un logger con los parámetros especificados"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Nivel de log desde la configuración
        logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        # Handler para archivo
        file_handler = logging.FileHandler(
            log_dir / f"{config.SERVICE_NAME}.log"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Evitar propagación a otros loggers
        logger.propagate = False
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Obtener un logger configurado"""
    return setup_logger(name)

def format_log_message(action: str, data: Dict[str, Any]) -> str:
    """Formatear un mensaje de log con datos estructurados"""
    timestamp = datetime.utcnow().isoformat()
    log_data = {
        "timestamp": timestamp,
        "service": config.SERVICE_NAME,
        "action": action,
        **data
    }
    return json.dumps(log_data)

def write(level: str, action: str, **kwargs: Any) -> None:
    """Escribir un mensaje de log estructurado"""
    logger = get_logger(__name__)
    msg = format_log_message(action, kwargs)
    
    level_method = getattr(logger, level.lower(), logger.info)
    level_method(msg)