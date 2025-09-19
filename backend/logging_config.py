import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "kubernetes_sd"):
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

    # File handler (rotating)
    fh = RotatingFileHandler(LOG_DIR / "backend.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def write(level: str, message: str, name: str = None, **meta):
    """Unified write helper. level: debug/info/warning/error. name: logger name (module).
    meta: arbitrary key/value pairs that will be appended to the message for context.
    """
    logger = get_logger(name or "kubernetes_sd")
    if meta:
        meta_str = " " + " ".join(f"{k}={v}" for k, v in meta.items())
    else:
        meta_str = ""
    msg = f"{message}{meta_str}"
    lvl = level.lower()
    if lvl == "debug":
        logger.debug(msg)
    elif lvl == "warning" or lvl == "warn":
        logger.warning(msg)
    elif lvl == "error":
        logger.error(msg)
    else:
        logger.info(msg)


def client_log(level: str, message: str, user: str = None, meta: dict = None):
    write(level, message, name="client", user=user, meta=meta)


def request_log(method: str, path: str, status: int, time: float, auth: bool = False, name: str = None):
    write("info", f"request {method} {path} status={status} time={time:.3f}s auth={auth}", name=name or "request")
