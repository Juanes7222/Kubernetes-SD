from fastapi import Depends, HTTPException, Header
from typing import Dict, Any, Optional
from services.task_service import firebase_auth_service

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependencia para obtener el usuario actual a partir del token de Firebase.
    Se espera un header: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        token_type, token = authorization.split()
        if token_type.lower() != "bearer":
            raise ValueError("Invalid token type")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    user = firebase_auth_service.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user