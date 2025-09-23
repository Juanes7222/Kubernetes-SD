import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Logs Service")
    DESCRIPTION: str = os.getenv("DESCRIPTION", "Logging Microservice")
    VERSION: str = os.getenv("VERSION", "2.0.0")

    CORS_ORIGINS: list[str] = ["*"]  # Logs service accepts from everywhere
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()