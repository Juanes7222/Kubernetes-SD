import firebase_admin
from firebase_admin import credentials, firestore, auth
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException
from pathlib import Path
from core.utils import to_firestore_dates, from_firestore_dates, safe_firebase_call
from core.logging_config import get_logger

logger = get_logger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        # Ruta al archivo de credenciales
        cred_path = Path(__file__).parent / '../secrets/kubernetes-sd.json'
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
                
            info = FirebaseAuthService.get_user_by_uid(uid)
            entry = {
                "uid": info.get("uid") if info else uid,
                "email": info.get("email") if info else None,
                "display_name": info.get("display_name") if info else None,
            }
            
            # Solo agregar si tenemos un uid válido
            if entry["uid"]:
                cache[uid] = entry
                resolved.append(entry)

        task["collaborators"] = resolved
        return task
    
    def _enrich_owner(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add basic information about the owner of the task
        """
        owner_id = task.get("owner_id") or task.get("user_id")
        
        if isinstance(owner_id, str) and owner_id:
            owner_info = FirebaseAuthService.get_user_by_uid(owner_id)
        else:
            owner_info = None
        
        task["owner"] = {
            "uid": owner_info.get("uid") if owner_info else owner_id,
            "email": owner_info.get("email") if owner_info else None,
            "display_name": owner_info.get("display_name") if owner_info else None,
        }
        return task
    
    def _enrich_assignee(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add basic information about the assigned person of the task
        """
        assigned_to = task.get("assigned_to")
        
        if isinstance(assigned_to, str) and assigned_to:
            assignee_info = FirebaseAuthService.get_user_by_uid(assigned_to)
        else:
            assignee_info = None
        
        task["assignee"] = {
            "uid": assignee_info.get("uid") if assignee_info else assigned_to,
            "email": assignee_info.get("email") if assignee_info else None,
            "display_name": assignee_info.get("display_name") if assignee_info else None,
        } if assigned_to else None
        return task
    
    def _enrich_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches collaborators, owner and assignee
        """
        task = self._enrich_collaborators(task)
        task = self._enrich_owner(task)
        task = self._enrich_assignee(task)
        return task
    
    def _enrich_task_for_user(self, task: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Enriches task with user-specific information like who invited them
        """
        task = self._enrich_task(task)
        
        # Agregar información de quién invitó al usuario actual si es colaborador
        collaborator_invites = task.get("collaborator_invites", {})
        if user_id in collaborator_invites:
            task["invited_by"] = collaborator_invites[user_id]
        
        return task


    def create_task(self, task_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
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
        return self._enrich_task(task_data)
    
    def get_tasks(self,
                  user_id: str,
                  search: Optional[str] = None,
                  only_owned: bool = False,
                  only_collab: bool = False,
                  only_assigned: bool = False
                ) -> List[Dict[str, Any]]:
        """
        Get tasks filtered by ownership/collaboration/assignment.
        - only_owned = True -> only tasks where user is owner
        - only_collab = True -> only tasks where user is a collaborator
        - only_assigned = True -> only tasks assigned to user
        - default -> all (owned + collaborative + assigned)
        """
        try:
            docs = []
            logger.info(f"get_tasks: Getting tasks for user_id={user_id}, only_owned={only_owned}, only_collab={only_collab}, only_assigned={only_assigned}")
            
            if not only_collab and not only_assigned:
                logger.info(f"get_tasks: Querying owned tasks for {user_id}")
                owned_docs = list(self.collection.where("owner_id", "==", user_id).stream())
                logger.info(f"get_tasks: Found {len(owned_docs)} owned tasks")
                docs += owned_docs
                
            if not only_owned and not only_assigned:
                logger.info(f"get_tasks: Querying collaborative tasks for {user_id}")
                collab_docs = list(self.collection.where("collaborators", "array_contains", user_id).stream())
                logger.info(f"get_tasks: Found {len(collab_docs)} collaborative tasks")
                docs += collab_docs
                
            if not only_owned and not only_collab:
                logger.info(f"get_tasks: Querying assigned tasks for {user_id}")
                assigned_docs = list(self.collection.where("assigned_to", "==", user_id).stream())
                logger.info(f"get_tasks: Found {len(assigned_docs)} assigned tasks")
                docs += assigned_docs
                
        except Exception as e:
            logger.error(f"get_tasks: Error querying tasks: {e}")
            raise HTTPException(status_code=500, detail="Error querying tasks")

        tasks = []
        seen_ids = set()
        for doc in docs:
            task = doc.to_dict()
            if not task:
                continue
            task["id"] = doc.id
            
            # Evitar duplicados
            if task["id"] in seen_ids:
                logger.info(f"get_tasks: skipping duplicate task {task['id']}")
                continue
            seen_ids.add(task["id"])
            
            if search:
                search_lower = search.lower()
                if search_lower in task.get("title", "").lower() or search_lower in task.get("description", "").lower():
                    tasks.append(self._enrich_task_for_user(task, user_id))
            else:
                tasks.append(self._enrich_task_for_user(task, user_id))

        logger.info(f"get_tasks: returning {len(tasks)} tasks after deduplication for user {user_id}")
        tasks.sort(key=lambda t: t.get("created_at") or datetime.fromtimestamp(0, tz=timezone.utc), reverse=True)
        return tasks
    
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
        return self._enrich_task_for_user(task, user_id)
    
    def update_task(self, task_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
        return self._enrich_task_for_user(updated_task, user_id)
    
    def delete_task(self, task_id: str, user_id: str) -> bool:
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
    
    def toggle_task_completion(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
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
        doc_ref.update({"completed": new_status})
        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
        updated_task["id"] = doc_ref.id
        return self._enrich_task_for_user(updated_task, user_id)

    # ---------------------------- Métodos para gestionar colaboradores ---------------------------- #

    def add_collaborator(self, task_id: str, owner_id: str, collaborator: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None
        if not task or (task.get("owner_id") or task.get("user_id")) != owner_id:
            # Solo el propietario puede invitar colaboradores
            return None
        
        # Obtener información del propietario que está agregando
        owner_info = FirebaseAuthService.get_user_by_uid(owner_id)
        
        collaborators = task.get("collaborators", [])
        collaborator_invites = task.get("collaborator_invites", {})
        
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
            # Guardar quién invitó a este colaborador
            collaborator_invites[collaborator_uid] = {
                "invited_by_uid": owner_id,
                "invited_by_email": owner_info.get("email") if owner_info else None,
                "invited_by_name": owner_info.get("display_name") if owner_info else None,
                "invited_at": datetime.now(timezone.utc).isoformat()
            }
            
            doc_ref.update({
                "collaborators": collaborators,
                "collaborator_invites": collaborator_invites
            })
        
        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
        updated_task["id"] = doc_ref.id
        logger.info(f"add_collaborator: task_id={task_id} owner_id={owner_id} added={collaborator_uid} collaborators={collaborators}")
        return self._enrich_task(updated_task)

    def remove_collaborator(self, task_id: str, owner_id: str, collaborator_uid: str) -> Optional[Dict[str, Any]]:
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
            user_info = FirebaseAuthService.get_user_by_email(collaborator_uid)
            if not user_info:
                logger.info(f"remove_collaborator: no user found for email {collaborator_uid}")
                return None
            to_remove = user_info['uid']

        if to_remove in collaborators:
            collaborators = [c for c in collaborators if c != to_remove]
            doc_ref.update({"collaborators": collaborators})

        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
        updated_task["id"] = doc_ref.id
        return self._enrich_task(updated_task)

    def assign_task(self, task_id: str, assignee: str, assigner_id: str) -> Optional[Dict[str, Any]]:
        """
        Asignar una tarea a un responsable.
        Solo el propietario o colaboradores pueden asignar tareas.
        """
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None
        
        if not task:
            return None
            
        # Verificar que el usuario que asigna tiene permisos (owner o colaborador)
        owner_id = task.get("owner_id") or task.get("user_id")
        collaborators = task.get("collaborators", [])
        
        if assigner_id != owner_id and assigner_id not in collaborators:
            logger.warning(f"assign_task: user {assigner_id} not authorized to assign task {task_id}")
            return None
        
        # Si el 'assignee' contiene '@' tratamos como email y resolvemos a uid
        assignee_uid = assignee
        if "@" in assignee:
            user_info = FirebaseAuthService.get_user_by_email(assignee)
            if not user_info:
                logger.warning(f"assign_task: no user found for email {assignee}")
                return None
            assignee_uid = user_info['uid']
        
        # Actualizar la asignación
        doc_ref.update({"assigned_to": assignee_uid})
        
        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
        updated_task["id"] = doc_ref.id
        logger.info(f"assign_task: task {task_id} assigned to {assignee_uid} by {assigner_id}")
        return self._enrich_task(updated_task)

    def unassign_task(self, task_id: str, assigner_id: str) -> Optional[Dict[str, Any]]:
        """
        Desasignar una tarea (quitar responsable).
        Solo el propietario o colaboradores pueden desasignar tareas.
        """
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        task = doc.to_dict() if doc else None
        
        if not task:
            return None
            
        # Verificar que el usuario que desasigna tiene permisos (owner o colaborador)
        owner_id = task.get("owner_id") or task.get("user_id")
        collaborators = task.get("collaborators", [])
        
        if assigner_id != owner_id and assigner_id not in collaborators:
            logger.warning(f"unassign_task: user {assigner_id} not authorized to unassign task {task_id}")
            return None
        
        # Remover la asignación
        doc_ref.update({"assigned_to": None})
        
        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
        updated_task["id"] = doc_ref.id
        logger.info(f"unassign_task: task {task_id} unassigned by {assigner_id}")
        return self._enrich_task(updated_task)


# Create service instances
firebase_auth_service = FirebaseAuthService()
firebase_service = FirebaseTaskService()