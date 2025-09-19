from fastapi import APIRouter, Depends, Request
from typing import Optional
from core.logging_config import get_logger, client_log, write

logger = get_logger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("/client")
async def ingest_client_log(request: Request):
    """Accept a small JSON payload from client-side with keys: level, message, user (optional), meta (optional)"""
    body = await request.json()
    level = body.get("level", "info").lower()
    message = body.get("message", "")
    user = body.get("user")
    meta = body.get("meta")

    # Use centralized client_log helper
    client_log(level, message, user=user, meta=meta)
    return {"status": "ok"}


@router.get("/test")
async def test_logging():
    """Emits sample logs at different levels to test logging pipeline."""
    write("debug", "test_logging: debug message", name=__name__)
    write("info", "test_logging: info message", name=__name__)
    write("warning", "test_logging: warning message", name=__name__)
    write("error", "test_logging: error message", name=__name__)
    return {"status": "ok", "message": "logs emitted"}
