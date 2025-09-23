from fastapi import APIRouter, Depends, HTTPException
from core.auth_middleware import get_current_user
from services.auth_service import firebase_auth_service
from models.schemas import User
from typing import Dict, Any
from core.logging_config import write

router = APIRouter(tags=["auth"])

@router.get("/verify")
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Verify token and return user info"""
    user_info = firebase_auth_service.get_user_by_uid(current_user["uid"])
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    write("info", "token_verified", user=current_user.get("email") or current_user.get("uid"))
    return User(**user_info)

@router.get("/users/{uid}", response_model=User)
async def get_user_by_uid(uid: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return basic user info for a given UID"""
    user_info = firebase_auth_service.get_user_by_uid(uid)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    write("info", "get_user_by_uid", requested_uid=uid, by_user=current_user.get("uid"))
    return User(**user_info)

@router.get("/users/email/{email}", response_model=User)
async def get_user_by_email(email: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return basic user info for a given email"""
    user_info = firebase_auth_service.get_user_by_email(email)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    write("info", "get_user_by_email", email=email, by_user=current_user.get("uid"))
    return User(**user_info)