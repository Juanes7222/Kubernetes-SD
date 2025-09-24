from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import requests
from core import config
from core.logging_config import get_logger

# Configuración de seguridad para Bearer token
security = HTTPBearer(auto_error=True)

logger = get_logger(__name__)

async def verify_token(token: str) -> Dict[str, Any]:
    """
    Verifys an auth token with the auth service and returns user info if valid.
    Returns None if the token is invalid or an error occurs
    """
    try:
        response = requests.get(
            f"{config.AUTH_SERVICE_URL}/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return response.json()
        logger.error(f"Token verification error: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error connecting to the authentication service: {e}")
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get the current user from the auth token.
    Uses FastAPI's HTTPBearer for token validation.
    """
    token = credentials.credentials
    user = await verify_token(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    return user