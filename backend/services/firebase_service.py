import firebase_admin
import os
from firebase_admin import credentials, firestore, auth
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException
from pathlib import Path
from google.api_core.exceptions import FailedPrecondition
from core.utils import to_firestore_dates, get_path_credentials
from logging_config import get_logger

logger = get_logger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        # Ruta al archivo de credenciales
        cred_path = get_path_credentials()
            
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()


class FirebaseAuthService:
    """Service for Firebase Authentication"""
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return user info"""
        try:
            return auth.verify_id_token(token)
        except Exception as e:
            logger.exception(f"Token verification failed: {e}")
            return None
    
    @staticmethod
    def get_user_by_uid(uid: str) -> Optional[Dict[str, Any]]:
        """Get user information by UID"""
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
        """Get user information by email"""
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


class FirebaseTaskService:
    def __init__(self):
        self.collection = db.collection('tasks')

    def _enrich_collaborators(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve collaborator UIDs to basic user info to return to clients."""
        collaborators = task.get("collaborators") or []
        if not collaborators:
            task["collaborators"] = []
            return task

        resolved = []
        cache: Dict[str, Dict[str, Any]] = {}
        for uid in collaborators:
            if uid in cache:
                resolved.append(cache[uid])
                continue
            info = FirebaseAuthService.get_user_by_uid(uid)
            if info:
                entry = {"uid": info.get("uid"), "email": info.get("email"), "display_name": info.get("display_name")}
            else:
                entry = {"uid": uid, "email": None, "display_name": None}
            cache[uid] = entry
            resolved.append(entry)

        task["collaborators"] = resolved
        return task
    
    def create_task(self, task_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new task for a specific user"""
        task_data = to_firestore_dates(task_data)
        # Guardar owner_id para soporte de colaboración
        task_data["owner_id"] = user_id
        # Inicializar colaboradores si no existe
        if "collaborators" not in task_data:
            task_data["collaborators"] = []
        if not task_data.get("created_at"):
            task_data["created_at"] = datetime.now(timezone.utc)

        doc_ref = self.collection.document()  # Genera un ID único
        doc_ref.set(task_data)
        task_data["id"] = doc_ref.id
        return task_data
    
    def get_tasks(self, user_id: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks for a specific user with optional search"""
        try:
            # Obtener tareas donde sea owner o esté en collaborators
            # Firestore no soporta fácilmente OR con array-contains-any + equals en un solo query,
            # así que obtenemos las tareas donde owner == user_id y luego las donde collaborators contiene user_id
            docs_owner = self.collection.where("owner_id", "==", user_id).stream()
            docs_collab = self.collection.where("collaborators", "array_contains", user_id).stream()
            # Unir generadores
            docs = list(docs_owner) + list(docs_collab)
        except Exception:
            raise HTTPException(status_code=500, detail="Error querying tasks")

        tasks = []
        for doc in docs:
            task = doc.to_dict()
            task["id"] = doc.id
            if search:
                search_lower = search.lower()
                if search_lower in task.get("title", "").lower() or search_lower in task.get("description", "").lower():
                    tasks.append(task)
            else:
                tasks.append(task)

        # Ordenar por created_at descendente
        def _created_at_key(t):
            val = t.get("created_at")
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val)
                except Exception:
                    return datetime.fromtimestamp(0, tz=timezone.utc)
            return datetime.fromtimestamp(0, tz=timezone.utc)

        tasks.sort(key=_created_at_key, reverse=True)
        # Enrich collaborators for each task
        return [self._enrich_collaborators(t) for t in tasks]
    
    def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single task by ID for a specific user"""
        doc = self.collection.document(task_id).get()
        if not doc.exists:
            logger.info("get_task_by_id: not found task_id=%s user=%s", task_id, user_id)
            return None
        task = doc.to_dict()
        # Permitir acceso si es owner o está en collaborators
        if not task:
            logger.info("get_task_by_id: empty task data task_id=%s", task_id)
            return None
        owner = task.get("owner_id") or task.get("user_id")
        collaborators = task.get("collaborators") or []
        if owner != user_id and user_id not in collaborators:
            logger.info("get_task_by_id: access denied task_id=%s user=%s owner=%s", task_id, user_id, owner)
            return None
        task["id"] = doc.id
        return self._enrich_collaborators(task)
    
    def update_task(self, task_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task for a specific user"""
        update_data = to_firestore_dates(update_data)
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            logger.info("update_task: not found task_id=%s user=%s", task_id, user_id)
            return None
        task = doc.to_dict()
        # Solo owner o colaboradores pueden actualizar
        owner = task.get("owner_id") or task.get("user_id")
        collaborators = task.get("collaborators") or []
        if owner != user_id and user_id not in collaborators:
            logger.info("update_task: permission denied task_id=%s user=%s owner=%s", task_id, user_id, owner)
            return None
        doc_ref.update(update_data)
        updated_doc = doc_ref.get()
        task = updated_doc.to_dict()
        if not task:
            logger.info("update_task: updated doc empty task_id=%s", task_id)
            return None
        task["id"] = updated_doc.id
        return self._enrich_collaborators(task)
    
    def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task for a specific user"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            logger.info("delete_task: not found task_id=%s user=%s", task_id, user_id)
            return False
        task = doc.to_dict()
        # Solo owner puede eliminar (policy: solo owner borra)
        owner = task.get("owner_id") or task.get("user_id")
        if owner != user_id:
            logger.info("delete_task: permission denied task_id=%s user=%s owner=%s", task_id, user_id, owner)
            return False
        doc_ref.delete()
        return True
    
    def toggle_task_completion(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Toggle task completion status for a specific user"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            logger.info("toggle_task_completion: not found task_id=%s user=%s", task_id, user_id)
            return None
        task = doc.to_dict()
        # Owner o colaboradores pueden marcar completada
        owner = task.get("owner_id") or task.get("user_id")
        collaborators = task.get("collaborators") or []
        if owner != user_id and user_id not in collaborators:
            logger.info("toggle_task_completion: permission denied task_id=%s user=%s owner=%s", task_id, user_id, owner)
            return None
        new_status = not task.get("completed", False)
        doc_ref.update({"completed": new_status})
        updated_doc = doc_ref.get()
        task = updated_doc.to_dict()
        if not task:
            return None
        task["id"] = updated_doc.id
        return self._enrich_collaborators(task)

    # Métodos para gestionar colaboradores
    def add_collaborator(self, task_id: str, owner_id: str, collaborator: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        task = doc.to_dict()
        if not task:
            return None
        owner = task.get("owner_id") or task.get("user_id")
        if owner != owner_id:
            # Solo el propietario puede invitar colaboradores
            return None
        collaborators = task.get("collaborators") or []
        # Si el 'collaborator' contiene '@' tratamos como email y resolvemos a uid
        collaborator_uid = collaborator
        if "@" in collaborator:
            user_info = FirebaseAuthService.get_user_by_email(collaborator)
            if not user_info:
                # Usuario no existe
                return None
            collaborator_uid = user_info['uid']
        if collaborator_uid not in collaborators:
            collaborators.append(collaborator_uid)
            doc_ref.update({"collaborators": collaborators})
        task = doc_ref.get().to_dict()
        task["id"] = doc_ref.id
        logger.info(f"add_collaborator: task_id={task_id} owner={owner} added={collaborator_uid} collaborators={collaborators}")
        return self._enrich_collaborators(task)

    def remove_collaborator(self, task_id: str, owner_id: str, collaborator_uid: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        task = doc.to_dict()
        if not task:
            return None
        owner = task.get("owner_id") or task.get("user_id")
        if owner != owner_id:
            # Solo el propietario puede remover colaboradores
            return None
        collaborators = task.get("collaborators") or []
        # Permitir pasar email o uid para remover
        to_remove = collaborator_uid
        if "@" in collaborator_uid:
            user_info = FirebaseAuthService.get_user_by_email(collaborator_uid)
            if not user_info:
                logger.info(f"remove_collaborator: no user found for email {collaborator_uid}")
                return None
            to_remove = user_info['uid']
        logger.info(f"remove_collaborator: task_id={task_id} owner={owner} trying_remove={collaborator_uid} resolved={to_remove} collaborators_before={collaborators}")
        if to_remove in collaborators:
            collaborators = [c for c in collaborators if c != to_remove]
            doc_ref.update({"collaborators": collaborators})
            logger.info(f"remove_collaborator: removed {to_remove}, now collaborators={collaborators}")
        else:
            logger.info(f"remove_collaborator: {to_remove} not found in collaborators")
        task = doc_ref.get().to_dict()
        task["id"] = doc_ref.id
        return self._enrich_collaborators(task)


# Create service instances
firebase_auth_service = FirebaseAuthService()
firebase_service = FirebaseTaskService()