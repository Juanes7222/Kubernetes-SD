from core.firestore import db
from uuid import uuid4


class ListServices:

    @staticmethod
    def create_list(name: str, uid: str):
        """
        Crea una lista de tareas
        """
        list_id = str(uuid4)
        list_ref = db.collection("listas").document(list_id)
        list_ref.set({"id": list_id,
                      "nombre": name,
                      "miembros": [uid]})
        return {"message": f"La lista '{name}' ha sido creada exitosamente",
                "list_id": list_id}
    
    @staticmethod
    def get_lists(uid: str):
        """
        Retorna las listas a las que el usuario tiene acceso,
        con sus respectivas tareas
        """
        documents = db.collection("listas").where("miembros", "array_contains", uid).stream()
        lists = []
        for document in documents:
            data = document.to_dict()
            task_documents = db.collection("listas").document(data["id"]).collection("tareas").stream()
            task = [t.to_dict() for t in task_documents]
            lists.append({"id": data["id"], "name": data["name"], "tasks": task})
        return lists
