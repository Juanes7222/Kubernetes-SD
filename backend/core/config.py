import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Directorio raíz del proyecto
ROOT_DIR = Path(__file__).parent.parent

# Cargar variables de entorno desde .env
load_dotenv(ROOT_DIR / ".env")

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
    FIREBASE_CREDENTIALS = ROOT_DIR / "secrets" / "kubernetes-sd.json"

    # Flags
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()

# Logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)