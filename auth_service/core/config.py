import os

# Configuración básica del servicio
SERVICE_NAME = "auth_service"
PORT = int(os.getenv("PORT", 8000))
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "../secrets/kubernetes-sd.json")
