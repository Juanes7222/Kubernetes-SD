import logging
from typing import Any

def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )
    return logging.getLogger(name)

def write(level: str, action: str, **kwargs: Any):
    logger = get_logger(__name__)
    msg = f"{action} | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
    if level.lower() == "info":
        logger.info(msg)
    elif level.lower() == "error":
        logger.error(msg)
    elif level.lower() == "warning":
        logger.warning(msg)
    else:
        logger.debug(msg)
