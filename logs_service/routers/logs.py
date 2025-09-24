from fastapi import APIRouter, Request
from core.logging_config import client_log, write

router = APIRouter(tags=["logs"])

@router.post("/client")
async def ingest_client_log(request: Request):
    """Endpoint centralizado para recibir logs de todos los servicios"""
    body = await request.json()
    level = body.get("level", "info").lower()
    message = body.get("message", "")
    user = body.get("user")
    meta = body.get("meta", {})
    
    service = meta.get("service", "unknown")
    logger_name = meta.get("logger_name", "client")
    
    # Log centralizado - aquí SÍ se escribe en archivo
    client_log(level, f"[Service = {service}, logger_name = {logger_name}] {message}", user=user, meta=meta)
    return {"status": "ok", "received_from": service}

@router.get("/test")
async def test_logging():
    """Test endpoint - solo para el logs_service"""
    write("debug", "test_logging: debug message")
    write("info", "test_logging: info message")
    write("warning", "test_logging: warning message")
    write("error", "test_logging: error message")
    return {"status": "ok", "message": "logs emitted from logs_service"}