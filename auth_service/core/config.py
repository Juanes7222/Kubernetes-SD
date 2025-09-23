import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Auth Service")
    DESCRIPTION: str = os.getenv("DESCRIPTION", "Authentication Microservice")
    VERSION: str = os.getenv("VERSION", "2.0.0")

    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]
    
    # Firebase
    FIREBASE_CREDENTIALS = ROOT_DIR / "secrets" / "kubernetes-sd.json"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Services URLs
    LOGS_SERVICE_URL: str = os.getenv("LOGS_SERVICE_URL", "http://localhost:8001")

settings = Settings()