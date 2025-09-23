import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from core.logging_config import write
from core import config
import requests
from pathlib import Path


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
        self.collection = self.db.collection("tasks")

    def get_user_info_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info from auth service"""
        try:
            response = requests.get(f"{config.AUTH_SERVICE_URL}/users/{user_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            write("error", f"Error getting user info: {e}")
            return None

    def get_user_info_by_email(self, user_email: str) -> Optional[Dict[str, Any]]:
        """Get user info from auth service by email"""
        try:
            response = requests.get(
                f"{config.AUTH_SERVICE_URL}/users/email/{user_email}"
            )
            if response.status_code == 200:
                users = response.json()
                if users:
                    return users[0]  # Assuming the first match is the desired user
            return None
        except Exception as e:
            write("error", f"Error getting user info by email: {e}")
            return None
   
    def get_user_info(self, user_identifier: str) -> Optional[Dict[str, Any]]:
        """Get user info by UID or email"""
        if "@" in user_identifier:
            return self.get_user_info_by_email(user_identifier)
        else:
            return self.get_user_info_by_id(user_identifier)

    def add_collaborator(
        self, task_id: str, owner_id: str, collaborator: str
    ) -> Optional[Dict[str, Any]]:
        """Add a collaborator to a task"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None

        if not task or task.get("owner_id") != owner_id:
            write(
                "info", f"Task {task_id} not found or access denied for user {owner_id}"
            )
            return None

        collaborators = task.get("collaborators", [])

        # Determinar el UID del colaborador
        collaborator_uid = collaborator
        user_info = self.get_user_info(collaborator)      
        collaborator_uid = user_info.get("uid")
        
        # Evitar duplicados
        if collaborator_uid not in collaborators:
            collaborators.append(collaborator_uid)

            # Actualizar la tarea
            doc_ref.update(
                {
                    "collaborators": collaborators,
                    "updated_at": datetime.now(timezone.utc),
                }
            )

            # Obtener la tarea actualizada
            updated_task = doc_ref.get().to_dict()
            if not updated_task:
                return None

            write(
                "info",
                f"Collaborator {collaborator_uid} added to task {task_id} "
                f"by {owner_id}"
            )
            return self._enrich_collaborators(updated_task)
        return self._enrich_collaborators(task)

    def remove_collaborator(
        self, task_id: str, owner_id: str, collaborator_uid: str
    ) -> Optional[Dict[str, Any]]:
        """Delete a collaborator from a task"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None

        if not task or task.get("owner_id") != owner_id:
            write(
                "info"
                f"Task {task_id} not found or access denied for user {owner_id}"
            )
            return None

        collaborators = task.get("collaborators", [])
        user_info = self.get_user_info(collaborator_uid)      
        collaborator_uid = user_info.get("uid")

        # Remover el colaborador si existe
        if collaborator_uid in collaborators:
            collaborators.remove(collaborator_uid)

            # Actualizar la tarea
            doc_ref.update(
                {
                    "collaborators": collaborators,
                    "updated_at": datetime.now(timezone.utc),
                }
            )

            # Obtener la tarea actualizada
            updated_task = doc_ref.get().to_dict()
            if not updated_task:
                return None

            write(
               "info",
                f"Collaborator {collaborator_uid} removed from task {task_id} "
                f"by {owner_id}"
            )
            return self._enrich_collaborators(updated_task)
        return self._enrich_collaborators(task)

    def get_collaborators(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get collaborators of a task"""
        doc = self.collection.document(task_id).get()
        if not doc.exists:
            write("info", f"Task {task_id} not found")
            return None

        task = doc.to_dict()
        if not task:
            return None

        # Verificar acceso (debe ser owner o colaborador)
        if task.get("owner_id") != user_id and user_id not in task.get(
            "collaborators", []
        ):
            write("info", f"Access denied for task {task_id} to user {user_id}")
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

        return {"task_id": task.get("id"), "collaborators": enriched_collaborators}


collaborator_service = CollaboratorService()
