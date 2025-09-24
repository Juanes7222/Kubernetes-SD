import os
from pathlib import Path
from typing import List, Optional
from functools import lru_cache
from dotenv import load_dotenv

# Cargar variables de entorno
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / "secrets/.env")

class Settings():
    # Información básica del servicio
    PROJECT_NAME: str = "Auth Service"
    DESCRIPTION: str = "Authentication Microservice for Kubernetes-SD"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Configuración del servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"

    # Configuración de seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura_aqui")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: Path = ROOT_DIR / "secrets" / "kubernetes-sd.json"
    
    # URLs de servicios
    LOGS_SERVICE_URL: str = os.getenv("LOGS_SERVICE_URL", "http://localhost:8001")
    TASKS_SERVICE_URL: str = os.getenv("TASKS_SERVICE_URL", "http://localhost:8002")
    COLLABORATOR_SERVICE_URL: str = os.getenv("COLLABORATOR_SERVICE_URL", "http://localhost:8003")

    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # LOG_FILE: Optional[Path] = ROOT_DIR / "logs" / "auth_service.log"


@lru_cache()
def get_settings() -> Settings:
    """
    Get a cached instance of the settings.
    This avoids loading the .env file multiple times.
    """
    return Settings()

# Instancia global de configuración
settings = get_settings()