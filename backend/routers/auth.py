from fastapi import APIRouter, Depends, HTTPException
from core.auth_middleware import get_current_user
from services.firebase_service import firebase_auth_service
from models.schemas import User
from typing import Dict, Any
from core.logging_config import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])

logger = get_logger(__name__)


def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_info = firebase_auth_service.get_user_by_uid(current_user["uid"])
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("get_current_user_info: user=%s", current_user.get("email") or current_user.get("uid"))
    return User(**user_info)