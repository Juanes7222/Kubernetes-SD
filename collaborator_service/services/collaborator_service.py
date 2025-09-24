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

    def get_user_info_by_id(self, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        """Get user info from auth service"""
        try:
            response = requests.get(
                f"{config.AUTH_SERVICE_URL}/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            write("error", f"Error getting user info: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            write("error", f"Error getting user info: {e}")
            return None

    def get_user_info_by_email(self, user_email: str, token: str) -> Optional[Dict[str, Any]]:
        """Get user info from auth service by email"""
        try:
            response = requests.get(
                f"{config.AUTH_SERVICE_URL}/users/email/{user_email}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            write("error", f"Error getting user info by email: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            write("error", f"Error getting user info by email: {e}")
            return None
   
    def get_user_info(self, user_identifier: str, token: str) -> Optional[Dict[str, Any]]:
        """Get user info by UID or email"""
        if "@" in user_identifier:
            return self.get_user_info_by_email(user_identifier, token)
        else:
            return self.get_user_info_by_id(user_identifier, token)

    def add_collaborator(
        self, task_id: str, owner_id: str, collaborator: str, token: str
    ) -> Optional[Dict[str, Any]]:
        """Add a collaborator to a task"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None

        if not task:
            write("error", f"Task {task_id} not found")
            return None

        if task.get("owner_id") != owner_id:
            write("error", f"Access denied for user {owner_id} on task {task_id}")
            return None

        # Determinar el UID del colaborador
        user_info = self.get_user_info(collaborator, token)
        if not user_info:
            write("error", f"User {collaborator} not found")
            return None

        collaborator_uid = user_info.get("uid")
        if not collaborator_uid:
            write("error", f"Invalid user info for {collaborator}")
            return None

        # Evitar que el propietario se añada como colaborador
        if collaborator_uid == owner_id:
            write("error", f"Owner cannot be added as collaborator")
            return None

        collaborators = task.get("collaborators", [])
        
        # Evitar duplicados
        if collaborator_uid in collaborators:
            write("info", f"User {collaborator_uid} is already a collaborator")
            return self._enrich_collaborators(task, token)

        collaborators.append(collaborator_uid)

        # Actualizar la tarea
        update_data = {
            "collaborators": collaborators,
            "updated_at": datetime.now(timezone.utc),
        }

        try:
            doc_ref.update(update_data)
            # Obtener la tarea actualizada
            updated_task = doc_ref.get().to_dict()
            if not updated_task:
                write("error", f"Error retrieving updated task {task_id}")
                return None
                
            updated_task["id"] = task_id  # Asegurar que el ID está presente

            write(
                "info",
                f"Collaborator {collaborator_uid} added to task {task_id} by {owner_id}"
            )
            return self._enrich_collaborators(updated_task, token)
        except Exception as e:
            write("error", f"Error updating task {task_id}: {str(e)}")
            return None 

    def remove_collaborator(
        self, task_id: str, owner_id: str, collaborator_uid: str, token: str
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
        user_info = self.get_user_info(collaborator_uid, token)      
        collaborator_uid = user_info.get("uid") if user_info else None
        
        if not collaborator_uid:
            write("error", f"Invalid collaborator info for {collaborator_uid}")
            return None

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
            
            updated_task["id"] = task_id  # Asegurar que el ID está presente

            write(
               "info",
                f"Collaborator {collaborator_uid} removed from task {task_id} "
                f"by {owner_id}"
            )
            return self._enrich_collaborators(updated_task, token)
        return self._enrich_collaborators(task, token)

    def get_collaborators(self, task_id: str, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        """Get collaborators of a task"""
        doc = self.collection.document(task_id).get()
        if not doc.exists:
            write("info", f"Task {task_id} not found")
            return None

        task = doc.to_dict()
        if not task:
            return None
            
        task["id"] = task_id  # Asegurar que el ID está en el documento

        # Verificar acceso (debe ser owner o colaborador)
        if task.get("owner_id") != user_id and user_id not in task.get(
            "collaborators", []
        ):
            write("info", f"Access denied for task {task_id} to user {user_id}")
            return None

        # Enriquecer con información de usuarios y devolver
        enriched_task = self._enrich_collaborators(task, token)
        return enriched_task

    def _enrich_collaborators(self, task: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Enrich collaborator UIDs with user info"""
        if not task:
            write("error", "Cannot enrich collaborators for None task")
            return None

        task_id = task.get("id")
        if not task_id:
            write("error", f"Task has no valid ID: {task}")
            return None

        # Procesar colaboradores
        collaborators = task.get("collaborators", [])
        enriched_collaborators = []

        for uid in collaborators:
            user_info = self.get_user_info(uid, token)
            if user_info:
                collaborator = {
                    "uid": uid,
                    "email": user_info.get("email"),
                    "display_name": user_info.get("display_name"),
                }
                enriched_collaborators.append(collaborator)

        # Devolver el formato esperado por CollaboratorResponse
        return {
            "task_id": task_id,
            "collaborators": enriched_collaborators
        }


collaborator_service = CollaboratorService()
