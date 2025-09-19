import firebase_admin
from firebase_admin import credentials, firestore, auth
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException
from pathlib import Path
from google.api_core.exceptions import FailedPrecondition
from core.utils import to_firestore_dates, from_firestore_dates, safe_firebase_call

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
    
    def create_task(self, task_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new task for a specific user"""
        task_data = to_firestore_dates(task_data)
        task_data["user_id"] = user_id
        if not task_data.get("created_at"):
            task_data["created_at"] = datetime.now(timezone.utc)

        doc_ref = self.collection.document()  # Genera un ID único
        doc_ref.set(task_data)
        task_data["id"] = doc_ref.id
        return task_data
    
    def get_tasks(self, user_id: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks for a specific user with optional search"""
        try:
            query = self.collection.where("user_id", "==", user_id)
            docs = query.stream()
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
        return tasks
    
    def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single task by ID for a specific user"""
        doc = self.collection.document(task_id).get()
        if not doc.exists:
            return None
        task = doc.to_dict()
        if not task or task.get("user_id") != user_id:
            return None
        task["id"] = doc.id
        return task
    
    def update_task(self, task_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task for a specific user"""
        update_data = to_firestore_dates(update_data)
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        task = doc.to_dict()
        if not task or task.get("user_id") != user_id:
            return None
        doc_ref.update(update_data)
        updated_doc = doc_ref.get()
        task = updated_doc.to_dict()
        if not task:
            return None
        task["id"] = updated_doc.id
        return task
    
    def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task for a specific user"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        task = doc.to_dict()
        if not task or task.get("user_id") != user_id:
            return False
        doc_ref.delete()
        return True
    
    def toggle_task_completion(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Toggle task completion status for a specific user"""
        doc_ref = self.collection.document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        task = doc.to_dict()
        if not task or task.get("user_id") != user_id:
            return None
        new_status = not task.get("completed", False)
        doc_ref.update({"completed": new_status})
        updated_doc = doc_ref.get()
        task = updated_doc.to_dict()
        if not task:
            return None
        task["id"] = updated_doc.id
        return task


# Create service instances
firebase_auth_service = FirebaseAuthService()
firebase_service = FirebaseTaskService()