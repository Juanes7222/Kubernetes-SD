from fastapi import FastAPI
from routers import tasks
from core.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Tasks Service",
    version="1.0.0",
    description="Microservicio de gestión de tareas con Firebase"
)

# Incluir routers
app.include_router(tasks.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}