import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from core.logging_config import get_logger
from core import config
import requests
from pathlib import Path

logger = get_logger(__name__)

def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = Path(config.FIREBASE_CRED_PATH)
        if not cred_path.is_file():
            raise FileNotFoundError(f"Firebase credentials not found at {cred_path}")
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
    return firestore.client()

class CollaboratorService:
    def __init__(self):
        self.db = initialize_firebase()
        self.collection = self.db.collection('tasks')

    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info from auth service"""
        try:
            response = requests.get(f"{config.AUTH_SERVICE_URL}/users/{user_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

    def add_collaborator(self, task_id: str, owner_id: str, collaborator: str) -> Optional[Dict[str, Any]]:
        """Add a collaborator to a task"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None

        if not task or task.get("owner_id") != owner_id:
            logger.info(f"Task {task_id} not found or access denied for user {owner_id}")
            return None

        collaborators = task.get("collaborators", [])

        # Determinar el UID del colaborador
        collaborator_uid = collaborator
        if "@" in collaborator:
            # Si es email, obtener el UID correspondiente
            user_info = self.get_user_info(collaborator)
            if not user_info:
                logger.info(f"User not found for email {collaborator}")
                return None
            collaborator_uid = user_info.get("uid")

        # Validar que el colaborador exista
        collaborator_info = self.get_user_info(collaborator_uid)
        if not collaborator_info:
            logger.info(f"User not found for uid {collaborator_uid}")
            return None

        # Evitar duplicados
        if collaborator_uid not in collaborators:
            collaborators.append(collaborator_uid)
            
            # Actualizar la tarea
            doc_ref.update({
                "collaborators": collaborators,
                "updated_at": datetime.now(timezone.utc)
            })

            # Obtener la tarea actualizada
            updated_task = doc_ref.get().to_dict()
            if not updated_task:
                return None

            logger.info(
                f"Collaborator {collaborator_uid} added to task {task_id} "
                f"by {owner_id}"
            )
            return self._enrich_collaborators(updated_task)
        return self._enrich_collaborators(task)

    def remove_collaborator(self, task_id: str, owner_id: str, collaborator_uid: str) -> Optional[Dict[str, Any]]:
        """Delete a collaborator from a task"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None

        if not task or task.get("owner_id") != owner_id:
            logger.info(f"Task {task_id} not found or access denied for user {owner_id}")
            return None

        collaborators = task.get("collaborators", [])

        # Si el colaborador es un email, obtener su UID
        if "@" in collaborator_uid:
            user_info = self.get_user_info(collaborator_uid)
            if not user_info:
                logger.info(f"User not found for email {collaborator_uid}")
                return None
            collaborator_uid = user_info.get("uid")

        # Remover el colaborador si existe
        if collaborator_uid in collaborators:
            collaborators.remove(collaborator_uid)

            # Actualizar la tarea
            doc_ref.update({
                "collaborators": collaborators,
                "updated_at": datetime.now(timezone.utc)
            })

            # Obtener la tarea actualizada
            updated_task = doc_ref.get().to_dict()
            if not updated_task:
                return None

            logger.info(
                f"Collaborator {collaborator_uid} removed from task {task_id} "
                f"by {owner_id}"
            )
            return self._enrich_collaborators(updated_task)
        return self._enrich_collaborators(task)

    def get_collaborators(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get collaborators of a task"""
        doc = self.collection.document(task_id).get()
        if not doc.exists:
            logger.info(f"Task {task_id} not found")
            return None

        task = doc.to_dict()
        if not task:
            return None

        # Verificar acceso (debe ser owner o colaborador)
        if (task.get("owner_id") != user_id and 
            user_id not in task.get("collaborators", [])):
            logger.info(f"Access denied for task {task_id} to user {user_id}")
            return None

        return self._enrich_collaborators(task)

    def _enrich_collaborators(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich collaborator UIDs with user info"""
        collaborators = task.get("collaborators", [])
        enriched_collaborators = []

        for uid in collaborators:
            user_info = self.get_user_info(uid)
            if user_info:
                collaborator = {
                    "uid": uid,
                    "email": user_info.get("email"),
                    "display_name": user_info.get("display_name"),
                }
                enriched_collaborators.append(collaborator)

        return {
            "task_id": task.get("id"),
            "collaborators": enriched_collaborators
        }

collaborator_service = CollaboratorService()