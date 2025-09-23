import logging
from core.config import settings

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def write(level: str, action: str, **kwargs):
    logger = get_logger("logs_service")
    msg = f"{action} | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
    getattr(logger, level.lower(), logger.info)(msg)