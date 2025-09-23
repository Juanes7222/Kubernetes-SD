import os

class Settings:
    ENV: str = os.getenv("ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "../secrets/kubernetes-sd.json")

settings = Settings()