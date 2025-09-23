from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any
from services.auth_service import firebase_auth_service
from core.logging_config import write

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

@router.post("/token")
def login(token: str = Depends(oauth2_scheme)):
    user_info = firebase_auth_service.verify_token(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    write("info", "login", name=__name__, user=user_info.get("email") or user_info.get("uid"))
    return {"access_token": token, "token_type": "bearer", "user": user_info}

@router.get("/me")
def get_current_user(token: str = Depends(oauth2_scheme)):
    user_info = firebase_auth_service.verify_token(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return user_info