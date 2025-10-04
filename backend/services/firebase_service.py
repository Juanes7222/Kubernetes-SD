import firebase_admin
import os
from firebase_admin import credentials, firestore, auth
from firebase_admin import _auth_utils
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException
from core.utils import to_firestore_dates, from_firestore_dates, get_path_credentials
from core.logging_config import get_logger

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
    async def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return user info"""
        try:
            # Firebase auth operations are CPU-bound, so we run them in a thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, auth.verify_id_token, token)
        except Exception as e:
            logger.exception(f"Token verification failed: {e}")
            return None
    
    @staticmethod
    async def get_user_by_uid(uid: str) -> Optional[Dict[str, Any]]:
        """Get user information by UID"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            user = await loop.run_in_executor(None, auth.get_user, uid)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'email_verified': user.email_verified,
                'disabled': user.disabled,
                'created_at': user.user_metadata.creation_timestamp,
                'last_sign_in': user.user_metadata.last_sign_in_timestamp
            }
        except _auth_utils.UserNotFoundError:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró ningún usuario con el UID: {uid}"
            )
        except Exception as e:
            logger.exception(f"Get user failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error al buscar usuario en Firebase"
            )
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user information by email"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            user = await loop.run_in_executor(None, auth.get_user_by_email, email)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'email_verified': user.email_verified,
                'disabled': user.disabled,
                'created_at': user.user_metadata.creation_timestamp,
                'last_sign_in': user.user_metadata.last_sign_in_timestamp
            }
        except _auth_utils.UserNotFoundError:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró ningún usuario con el correo: {email}"
            )
        except Exception as e:
            logger.exception(f"Get user by email failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error al buscar usuario en Firebase"
            )


class FirebaseTaskService:
    def __init__(self):
        self.collection = db.collection('tasks')


    async def _enrich_collaborators(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve collaborator UIDs to basic user info to return to clients."""
        collaborators = task.get("collaborators") or []
        if not collaborators:
            task["collaborators"] = []
            return task

        resolved = []
        cache: Dict[str, Dict[str, Any]] = {}
        for collaborator in collaborators:
            # Asegurar que collaborator sea un string (UID)
            uid = collaborator if isinstance(collaborator, str) else collaborator.get("uid") if isinstance(collaborator, dict) else str(collaborator)
            
            # Saltear si uid es None o vacío
            if not uid or uid == "None":
                logger.warning(f"_enrich_collaborators: skipping invalid uid: {uid}")
                continue
            
            if uid in cache:
                resolved.append(cache[uid])
                continue
            
            # Intentar obtener información del usuario, pero continuar si no existe
            try:
                info = await FirebaseAuthService.get_user_by_uid(uid)
                entry = {
                    "uid": info.get("uid"),
                    "email": info.get("email"),
                    "display_name": info.get("display_name"),
                }
            except HTTPException:
                # Usuario no existe o error - usar solo el UID
                logger.warning(f"_enrich_collaborators: user not found for uid {uid}")
                entry = {
                    "uid": uid,
                    "email": None,
                    "display_name": None,
                }
            
            # Solo agregar si tenemos un uid válido
            if entry["uid"]:
                cache[uid] = entry
                resolved.append(entry)

        task["collaborators"] = resolved
        return task
    
    async def _enrich_owner(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add basic information about the owner of the task
        """
        owner_id = task.get("owner_id") or task.get("user_id")
        
        if isinstance(owner_id, str) and owner_id:
            try:
                owner_info = await FirebaseAuthService.get_user_by_uid(owner_id)
            except HTTPException:
                # Owner no existe - usar solo el UID
                logger.warning(f"_enrich_owner: owner not found for uid {owner_id}")
                owner_info = None
        else:
            owner_info = None
        
        task["owner"] = {
            "uid": owner_info.get("uid") if owner_info else owner_id,
            "email": owner_info.get("email") if owner_info else None,
            "display_name": owner_info.get("display_name") if owner_info else None,
        }
        return task
    
    async def _enrich_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches collaborators, owner, and converts Firestore dates
        """
        task = from_firestore_dates(task)  # Convertir dates de Firestore
        task = await self._enrich_collaborators(task)
        task = await self._enrich_owner(task)
        return task
    
    async def _enrich_task_for_user(self, task: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Enriches task with user-specific information
        """
        task = await self._enrich_task(task)
        return task


    async def create_task(self, task_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new task for a specific user"""
        task_data = to_firestore_dates(task_data)
        # Guardar owner_id para soporte de colaboración
        task_data["owner_id"] = user_id
        # Inicializar colaboradores si no existe
        task_data.setdefault("collaborators", [])
        task_data.setdefault("created_at", datetime.now(timezone.utc))

        doc_ref = self.collection.document()
        doc_ref.set(task_data)
        task_data["id"] = doc_ref.id
        return await self._enrich_task(task_data)
    
    async def get_tasks(
        self,
        user_id: str,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks for a user (owned + collaborative).
        """
        try:
            docs = []
            logger.info(f"get_tasks: Getting tasks for user_id={user_id}")

            # Owned tasks
            owned_docs = list(self.collection.where("owner_id", "==", user_id).stream())
            logger.info(f"get_tasks: Found {len(owned_docs)} owned tasks")
            docs.extend(owned_docs)

            # Collaborative tasks
            collab_docs = list(self.collection.where("collaborators", "array_contains", user_id).stream())
            logger.info(f"get_tasks: Found {len(collab_docs)} collaborative tasks")
            docs.extend(collab_docs)

        except Exception as e:
            logger.error(f"get_tasks: Error querying tasks: {e}")
            raise HTTPException(status_code=500, detail="Error querying tasks")

        tasks = []
        seen_ids = set()
        search_lower = search.lower() if search else None

        for doc in docs:
            task = doc.to_dict()
            if not task:
                continue
            task["id"] = doc.id

            # Evitar duplicados
            if task["id"] in seen_ids:
                continue
            seen_ids.add(task["id"])

            # Filtro de búsqueda si corresponde
            if search_lower:
                if not (
                    search_lower in task.get("title", "").lower()
                    or search_lower in task.get("description", "").lower()
                ):
                    continue

            enriched_task = await self._enrich_task_for_user(task, user_id)
            tasks.append(enriched_task)

        logger.info(f"get_tasks: returning {len(tasks)} tasks after deduplication for user {user_id}")
        tasks.sort(
            key=lambda t: t.get("created_at") or datetime.fromtimestamp(0, tz=timezone.utc),
            reverse=True,
        )
        return tasks
    
    async def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
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
        return await self._enrich_task_for_user(task, user_id)
    
    async def update_task(self, task_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task for a specific user"""
        update_data = to_firestore_dates(update_data)
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None
        if not task:
            logger.info("update_task: task not found task_id=%s", task_id)
            return None
        # Solo owner o colaboradores pueden actualizar
        owner = task.get("owner_id") or task.get("user_id")
        collaborators = task.get("collaborators") or []
        if owner != user_id and user_id not in collaborators:
            logger.info("update_task: permission denied task_id=%s user=%s owner=%s", task_id, user_id, owner)
            return None
        doc_ref.update(update_data)
        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
        updated_task["id"] = doc_ref.id
        return await self._enrich_task_for_user(updated_task, user_id)
    
    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task for a specific user"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        # Solo owner puede eliminar (policy: solo owner borra)
        task = doc.to_dict() if doc else None
        if not task:
            logger.info("delete_task: task not found task_id=%s", task_id)
            return False
        owner = task.get("owner_id") or task.get("user_id")
        if owner != user_id:
            logger.info("delete_task: permission denied task_id=%s user=%s owner=%s", task_id, user_id, owner)
            return False
        doc_ref.delete()
        return True
    
    async def toggle_task_completion(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Toggle task completion status for a specific user"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None
        if not task:
            return None
        # Owner o colaboradores pueden marcar completada
        owner = task.get("owner_id") or task.get("user_id")
        collaborators = task.get("collaborators") or []
        if owner != user_id and user_id not in collaborators:
            logger.info("toggle_task_completion: permission denied task_id=%s user=%s owner=%s", task_id, user_id, owner)
            return None
        new_status = not task.get("completed", False)
        due_date = task.get("due_date")
        if new_status:
            due_date = datetime.now(timezone.utc)
        else:
            due_date = None
        doc_ref.update({"completed": new_status, "due_date": due_date})
        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
        updated_task["id"] = doc_ref.id
        return await self._enrich_task_for_user(updated_task, user_id)

    # ---------------------------- Métodos para gestionar colaboradores ---------------------------- #

    async def add_collaborator(self, task_id: str, owner_id: str, collaborator: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None
        if not task or (task.get("owner_id") or task.get("user_id")) != owner_id:
            # Solo el propietario puede invitar colaboradores
            return None
        
        collaborators = task.get("collaborators", [])
        
        # Si el 'collaborator' contiene '@' tratamos como email y resolvemos a uid
        collaborator_uid = collaborator
        if "@" in collaborator:
            # get_user_by_email lanzará HTTPException si no existe
            user_info = await FirebaseAuthService.get_user_by_email(collaborator)
            collaborator_uid = user_info['uid']
        else:
            # Validar que el UID exista - lanzará HTTPException si no existe
            user_info = await FirebaseAuthService.get_user_by_uid(collaborator_uid)
        
        if collaborator_uid not in collaborators:
            collaborators.append(collaborator_uid)
            doc_ref.update({"collaborators": collaborators})
        
        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
        updated_task["id"] = doc_ref.id
        logger.info(f"add_collaborator: task_id={task_id} owner_id={owner_id} added={collaborator_uid} collaborators={collaborators}")
        return await self._enrich_task(updated_task)

    async def remove_collaborator(self, task_id: str, owner_id: str, collaborator_uid: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None
        if not task or (task.get("owner_id") or task.get("user_id")) != owner_id:
            # Solo el propietario puede remover colaboradores
            return None
        collaborators = task.get("collaborators") or []
        # Permitir pasar email o uid para remover
        to_remove = collaborator_uid
        if "@" in collaborator_uid:
            # get_user_by_email lanzará HTTPException si no existe
            user_info = await FirebaseAuthService.get_user_by_email(collaborator_uid)
            to_remove = user_info['uid']

        if to_remove in collaborators:
            collaborators = [c for c in collaborators if c != to_remove]
            doc_ref.update({"collaborators": collaborators})

        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
        updated_task["id"] = doc_ref.id
        return await self._enrich_task(updated_task)

# Create service instances
firebase_auth_service = FirebaseAuthService()
firebase_service = FirebaseTaskService()