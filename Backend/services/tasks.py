from core.firestore import db
from fastapi import HTTPException
from uuid import uuid4
from models.schemas import Task

def _check_membership(list_id: str, uid: str):
    """
    Verifica:
        * Si la lista existe en la base de datos
        * Si el usuario pertenece a una lista dada
    """
    list_ref = db.collection("listas").document(list_id)
    list = list_ref.get()
    if not list.exists:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    data = list.to_dict()
    if not data or "miembros" not in data or uid not in data["miembros"]:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta lista")

class TaskServices:

    @staticmethod
    def create_task(list_id: str, task: Task, uid: str):
        """
        Crea una tarea para una lista dada
        """
        _check_membership(list_id, uid)
        task.id_task = str(uuid4())
        db.collection("listas").document(list_id).collection("tareas").document(task.id_task).set(task.model_dump())
        return task

