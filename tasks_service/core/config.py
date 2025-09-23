import os

SERVICE_NAME = "tasks_service"
PORT = int(os.getenv("PORT", 8001))
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "../secrets/kubernetes-sd.json")