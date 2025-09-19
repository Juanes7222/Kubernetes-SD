from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_service import firebase_auth_service
from typing import Dict, Any, Optional

