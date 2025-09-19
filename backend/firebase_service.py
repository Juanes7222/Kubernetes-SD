import firebase_admin
from firebase_admin import credentials, firestore, auth
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os
from pathlib import Path
from fastapi import HTTPException
from google.api_core.exceptions import FailedPrecondition

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        # Ruta al archivo de credenciales
        cred_path = Path(__file__).parent / 'secrets/kubernetes-sd.json'
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
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            print(f"Token verification failed: {e}")
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
            print(f"Get user failed: {e}")
            return None

class FirebaseTaskService:
    def __init__(self):
        self.collection = db.collection('tasks')
    
    async def create_task(self, task_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new task for a specific user"""
        # Add user_id and timestamp (asegurar created_at)
        task_data['user_id'] = user_id
        if not task_data.get('created_at'):
            task_data['created_at'] = datetime.now(timezone.utc)
        
        # Crear documento con id generado de forma fiable usando document().set()
        doc_ref = self.collection.document()  # genera un id único
        doc_ref.set(task_data)
        task_data['id'] = doc_ref.id
        
        return task_data
    
    async def get_tasks(self, user_id: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks for a specific user with optional search"""
        try:
            # Query tasks para el usuario (sin order_by para evitar requerir índice compuesto)
            query = self.collection.where('user_id', '==', user_id)
            docs = query.stream()
        except FailedPrecondition as e:
            # El error normalmente incluye una URL con la sugerencia de índice
            message = str(e)
            link = None
            if "You can create it here:" in message:
                # extraer la URL si existe
                try:
                    link = message.split("You can create it here:")[1].strip().split()[0]
                except Exception:
                    link = None
            detail = "Firestore query requires a composite index."
            if link:
                detail += f" You can create it here: {link}"
            raise HTTPException(status_code=500, detail=detail)
        except Exception as e:
            # Otros errores
            raise HTTPException(status_code=500, detail=f"Error querying tasks: {e}")
        
        tasks = []
        
        for doc in docs:
            task = doc.to_dict()
            task['id'] = doc.id
            
            # Apply search filter if provided
            if search:
                search_lower = search.lower()
                if (search_lower in task.get('title', '').lower() or 
                    search_lower in task.get('description', '').lower()):
                    tasks.append(task)
            else:
                tasks.append(task)
        
        # Ordenar en el cliente por created_at (descendente).
        # Soporta datetime o strings ISO; si falta created_at, lo manda al final.
        def _created_at_key(t):
            val = t.get('created_at')
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val)
                except Exception:
                    return datetime.fromtimestamp(0, tz=timezone.utc)
            return datetime.fromtimestamp(0, tz=timezone.utc)
        
        tasks.sort(key=_created_at_key, reverse=True)
        return tasks
    
    async def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single task by ID for a specific user"""
        doc = self.collection.document(task_id).get()
        if doc.exists:
            task = doc.to_dict()
            # Verify task belongs to user
            if task.get('user_id') == user_id:
                task['id'] = doc.id
                return task
        return None
    
    async def update_task(self, task_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task for a specific user"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        task = doc.to_dict()
        # Verify task belongs to user
        if task.get('user_id') != user_id:
            return None
        
        doc_ref.update(update_data)
        
        # Return updated task
        updated_doc = doc_ref.get()
        task = updated_doc.to_dict()
        task['id'] = updated_doc.id
        return task
    
    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task for a specific user"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return False
        
        task = doc.to_dict()
        # Verify task belongs to user
        if task.get('user_id') != user_id:
            return False
        
        doc_ref.delete()
        return True
    
    async def toggle_task_completion(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Toggle task completion status for a specific user"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        task = doc.to_dict()
        # Verify task belongs to user
        if task.get('user_id') != user_id:
            return None
        
        new_status = not task.get('completed', False)
        doc_ref.update({'completed': new_status})
        
        # Return updated task
        updated_doc = doc_ref.get()
        task = updated_doc.to_dict()
        task['id'] = updated_doc.id
        return task

# Create service instances
firebase_auth_service = FirebaseAuthService()
firebase_service = FirebaseTaskService()