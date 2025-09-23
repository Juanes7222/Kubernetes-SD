from pathlib import Path
import os

# Service Info
SERVICE_NAME = "collaborator_service"
VERSION = "1.0.0"
DESCRIPTION = "Microservicio de gestión de colaboradores para tareas"

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8004"))
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

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
TASKS_SERVICE_URL = os.getenv("TASKS_SERVICE_URL", "http://tasks-service:8001")