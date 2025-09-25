import firebase_admin
from firebase_admin import credentials, auth
from pathlib import Path
from typing import Optional, Dict, Any
from core.logging_config import get_logger

logger = get_logger(__name__)

# Inicializar Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = Path(__file__).parent / '../secrets/kubernetes-sd.json'
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)

initialize_firebase()

class FirebaseAuthService:
    """Servicio para autenticación con Firebase"""
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verifica token y retorna información del usuario"""
        try:
            return auth.verify_id_token(token)
        except Exception as e:
            logger.exception(f"Token verification failed: {e}")
            return None

    @staticmethod
    def get_user_by_uid(uid: str) -> Optional[Dict[str, Any]]:
        try:
            user = auth.get_user(uid)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'email_verified': user.email_verified,
                'disabled': user.disabled,
                'created_at': user.user_metadata.creation_timestamp,
                'last_sign_in': user.user_metadata.last_sign_in_timestamp
            }
        except Exception as e:
            logger.exception(f"Get user failed: {e}")
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        try:
            user = auth.get_user_by_email(email)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'email_verified': user.email_verified,
                'disabled': user.disabled,
                'created_at': user.user_metadata.creation_timestamp,
                'last_sign_in': user.user_metadata.last_sign_in_timestamp
            }
        except Exception as e:
            logger.exception(f"Get user by email failed: {e}")
            return None

firebase_auth_service = FirebaseAuthService()
