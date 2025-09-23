import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException
from core.logging_config import get_logger
from core.utils import to_firestore_dates
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

class TaskService:
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

    def create_task(self, task_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new task for a specific user"""
        task_data = to_firestore_dates(task_data)
        task_data["owner_id"] = user_id
        task_data["created_at"] = datetime.now(timezone.utc)
        task_data["updated_at"] = task_data["created_at"]

        doc_ref = self.collection.document()
        doc_ref.set(task_data)
        
        task_data["id"] = doc_ref.id
        return task_data

    def get_tasks(self, user_id: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks for a specific user, optionally filtered by a search term"""
        try:
            query = self.collection.where("owner_id", "==", user_id)
            docs = list(query.stream())

            tasks = []
            for doc in docs:
                task = doc.to_dict()
                if not task:
                    continue
                task["id"] = doc.id

                # Aplicar filtro de búsqueda si existe
                if search:
                    search_lower = search.lower()
                    if not (
                        search_lower in task.get("title", "").lower()
                        or search_lower in task.get("description", "").lower()
                    ):
                        continue
                
                tasks.append(task)

            logger.info(f"get_tasks: returning {len(tasks)} tasks for user {user_id}")
            tasks.sort(
                key=lambda t: t.get("created_at") or datetime.fromtimestamp(0, tz=timezone.utc),
                reverse=True,
            )
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            raise HTTPException(status_code=500, detail="Error retrieving tasks")

    def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task by ID"""
        doc = self.collection.document(task_id).get()
        if not doc.exists:
            logger.info(f"Task {task_id} not found")
            return None
            
        task = doc.to_dict()
        if not task:
            return None
            
        if task.get("owner_id") != user_id:
            logger.info(f"Access denied for task {task_id} to user {user_id}")
            return None
            
        task["id"] = doc.id
        return task

    def update_task(self, task_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a specific task"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return None

        update_data = to_firestore_dates(update_data)
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        doc_ref = self.collection.document(task_id)
        doc_ref.update(update_data)
        
        updated_task = doc_ref.get().to_dict()
        if not updated_task:
            return None
            
        updated_task["id"] = doc_ref.id
        return updated_task

    def delete_task(self, task_id: str, user_id: str) -> bool:
        """Eliminar una tarea"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return False
            
        self.collection.document(task_id).delete()
        return True

    def toggle_task_completion(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Toggle the completion status of a task"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return None

        new_status = not task.get("completed", False)
        return self.update_task(
            task_id,
            user_id,
            {"completed": new_status}
        )

task_service = TaskService()