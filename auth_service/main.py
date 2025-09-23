from fastapi import FastAPI
from routers import auth
from core.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="Microservicio de autenticación con Firebase"
)

# Incluir routers
app.include_router(auth.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}