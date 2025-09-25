import os
from pathlib import Path
from typing import List, Optional
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "secrets/.env")
# Service Info
SERVICE_NAME = "auth_service"
VERSION = "1.0.0"
DESCRIPTION = "Microservicio de gestión de autenticación"

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Paths
BASE_DIR = Path(__file__).parent.parent
SECRETS_DIR = BASE_DIR / "secrets"

# Firebase
FIREBASE_CRED_PATH = os.getenv(
    "FIREBASE_CRED_PATH",
    str(SECRETS_DIR / "kubernetes-sd.json")
)

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
