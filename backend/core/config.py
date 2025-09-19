import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from core.logging_config import get_logger
from core.utils import get_path_credentials

# Directorio raíz del proyecto
ROOT_DIR = Path(__file__).parent.parent

# Cargar variables de entorno desde .env
load_dotenv(ROOT_DIR / "secrets/.env")

class Settings:
    PROJECT_NAME: str = "ToDo API with Auth"
    DESCRIPTION: str = "ToDo List API with Firebase Authentication"
    VERSION: str = "2.0.0"

    # CORS
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]
    if "*" in CORS_ORIGINS:
        CORS_ORIGINS = ["*"]

    # Firebase
    FIREBASE_CREDENTIALS = get_path_credentials()

    # Flags
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()

# Logging global (use centralized logger to ensure handlers/format)
logger = get_logger(__name__)