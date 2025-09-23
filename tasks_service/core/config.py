from pathlib import Path
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv(Path(__file__).parent.parent / "secrets/.env")
# Service Info
SERVICE_NAME = "tasks_service"
VERSION = "1.0.0"
DESCRIPTION = "Microservicio de gestión de tareas"

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))
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

# Auth Service
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
COLLABORATOR_SERVICE_URL = os.getenv("COLLABORATOR_SERVICE_URL", "http://collaborator-service:8004")
LOGS_SERVICE_URL = os.getenv("LOGS_SERVICE_URL", "http://logs-service:8003/client")