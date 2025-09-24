import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings:
    # Service Info
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Logs Service")
    DESCRIPTION: str = os.getenv("DESCRIPTION", "Logging Microservice")
    VERSION: str = os.getenv("VERSION", "2.0.0")
    SERVICE_NAME: str = "logs_service"
    
    # Server Config
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8003"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]  # Logs service accepts from everywhere
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = str(ROOT_DIR / "logs" / "centralized.log")
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5
    
    # Authorized Services
    AUTHORIZED_SERVICES: list[str] = [
        "auth_service",
        "tasks_service",
        "collaborator_service",
        "logs_service"
    ]

settings = Settings()