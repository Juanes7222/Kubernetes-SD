from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, date

# Cargar variables de entorno
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Importar servicios Firebase y middleware de auth
try:
    from firebase_service import firebase_service, firebase_auth_service
    from auth_middleware import get_current_user, get_optional_user
    firebase_available = True
except Exception:
    # Atrapar cualquier excepción durante la importación/Inicialización de firebase
    firebase_available = False
    print("⚠️  Firebase service not available. Using mock data.")
    # Placeholders para evitar NameError cuando se usa Depends(get_current_user)
    from fastapi import HTTPException
    async def get_current_user():
        # Si el middleware no está disponible, devolvemos 501 cuando se intente usar
        raise HTTPException(status_code=501, detail="Auth middleware not available")
    async def get_optional_user():
        # Devuelve None para rutas que admiten usuario opcional
        return None

# Create the main app
app = FastAPI(title="ToDo API with Auth", description="ToDo List API with Firebase Authentication")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class User(BaseModel):
	uid: str
	email: str
	display_name: Optional[str] = None
	email_verified: bool = False

class Task(BaseModel):
	id: str = Field(default_factory=lambda: str(uuid.uuid4()))
	title: str
	description: str = ""
	due_date: Optional[date] = None
	completed: bool = False
	created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
	user_id: str

class TaskCreate(BaseModel):
	title: str
	description: str = ""
	due_date: Optional[date] = None

class TaskUpdate(BaseModel):
	title: Optional[str] = None
	description: Optional[str] = None
	due_date: Optional[date] = None
	completed: Optional[bool] = None

# Mock data for testing without Firebase
mock_tasks = []

# Agregar utilidades para conversión de fechas y manejo seguro de llamadas a Firebase
from fastapi import HTTPException  # ...existing code may already import this...

def _to_firestore_dates(data: dict) -> dict:
    """
    Convierte objetos date en ISO strings para Firestore.
    Modifica y devuelve el dict (no clona).
    """
    if not data:
        return data
    if data.get('due_date') and isinstance(data['due_date'], date):
        data['due_date'] = data['due_date'].isoformat()
    return data

def _from_firestore_dates(data: dict) -> dict:
    """
    Convierte cadenas ISO en date (si aplica). No falla si el formato es inesperado.
    """
    if not data:
        return data
    if data.get('due_date'):
        try:
            data['due_date'] = datetime.fromisoformat(data['due_date']).date()
        except Exception:
            logging.getLogger(__name__).debug("No se pudo parsear due_date: %s", data.get('due_date'))
            data['due_date'] = None
    return data

async def _safe_firebase_call(coro, *args, **kwargs):
    """
    Ejecuta la llamada a firebase_service de forma segura:
    - Si la función/coroutine lanza HTTPException, se re-lanza.
    - Para cualquier otra excepción se registra y se lanza HTTP 500.
    Soporta tanto callables sync como async.
    """
    logger = logging.getLogger(__name__)
    try:
        result = coro(*args, **kwargs)
        # Si es awaitable, await it
        if hasattr(result, "__await__"):
            return await result
        return result
    except HTTPException:
        # permitir que HTTPException pasen
        raise
    except Exception as e:
        logger.exception("Error en llamada a Firebase: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

# Routes
@api_router.get("/")
async def root():
	return {
		"message": "ToDo API with Authentication is running!",
		"firebase_available": firebase_available,
		"version": "2.0.0",
		"features": ["authentication", "user_specific_tasks"]
	}

@api_router.get("/health")
async def health_check():
	return {
		"status": "healthy",
		"firebase": firebase_available,
		"timestamp": datetime.now(timezone.utc).isoformat()
	}

# Authentication Routes
@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
	if not firebase_available:
		raise HTTPException(status_code=501, detail="Firebase not available")
	user_info = firebase_auth_service.get_user_by_uid(current_user['uid'])
	if not user_info:
		raise HTTPException(status_code=404, detail="User not found")
	return User(
		uid=user_info['uid'],
		email=user_info['email'],
		display_name=user_info.get('display_name'),
		email_verified=user_info.get('email_verified', False)
	)

if firebase_available:
	# Protected Firebase routes (require authentication)
	@api_router.post("/tasks", response_model=Task)
	async def create_task(
		task_input: TaskCreate,
		current_user: Dict[str, Any] = Depends(get_current_user)
	):
		task_dict = task_input.dict()
		task_dict = _to_firestore_dates(task_dict)
		created_task = await _safe_firebase_call(firebase_service.create_task, task_dict, current_user['uid'])
		created_task = _from_firestore_dates(created_task)
		return Task(**created_task)

	@api_router.get("/tasks", response_model=List[Task])
	async def get_tasks(
		search: Optional[str] = None,
		current_user: Dict[str, Any] = Depends(get_current_user)
	):
		tasks = await _safe_firebase_call(firebase_service.get_tasks, current_user['uid'], search)
		for task in tasks or []:
			_from_firestore_dates(task)
		return [Task(**task) for task in (tasks or [])]

	@api_router.get("/tasks/{task_id}", response_model=Task)
	async def get_task(
		task_id: str,
		current_user: Dict[str, Any] = Depends(get_current_user)
	):
		task = await _safe_firebase_call(firebase_service.get_task_by_id, task_id, current_user['uid'])
		if not task:
			raise HTTPException(status_code=404, detail="Task not found")
		_from_firestore_dates(task)
		return Task(**task)

	@api_router.put("/tasks/{task_id}", response_model=Task)
	async def update_task(
		task_id: str,
		task_update: TaskUpdate,
		current_user: Dict[str, Any] = Depends(get_current_user)
	):
		update_data = {k: v for k, v in task_update.dict().items() if v is not None}
		update_data = _to_firestore_dates(update_data)
		updated_task = await _safe_firebase_call(firebase_service.update_task, task_id, current_user['uid'], update_data)
		if not updated_task:
			raise HTTPException(status_code=404, detail="Task not found")
		updated_task = _from_firestore_dates(updated_task)
		return Task(**updated_task)

	@api_router.delete("/tasks/{task_id}")
	async def delete_task(
		task_id: str,
		current_user: Dict[str, Any] = Depends(get_current_user)
	):
		success = await _safe_firebase_call(firebase_service.delete_task, task_id, current_user['uid'])
		if not success:
			raise HTTPException(status_code=404, detail="Task not found")
		return {"message": "Task deleted successfully"}

	@api_router.patch("/tasks/{task_id}/toggle")
	async def toggle_task_completion(
		task_id: str,
		current_user: Dict[str, Any] = Depends(get_current_user)
	):
		updated_task = await _safe_firebase_call(firebase_service.toggle_task_completion, task_id, current_user['uid'])
		if not updated_task:
			raise HTTPException(status_code=404, detail="Task not found")
		updated_task = _from_firestore_dates(updated_task)
		return Task(**updated_task)

else:
	# Mock routes para testing sin Firebase
	@api_router.post("/tasks", response_model=Task)
	async def create_task_mock(task_input: TaskCreate):
		task = Task(**task_input.dict(), user_id="mock_user")
		mock_tasks.append(task.dict())
		return task

	@api_router.get("/tasks", response_model=List[Task])
	async def get_tasks_mock(search: Optional[str] = None):
		tasks = mock_tasks.copy()
		if search:
			search_lower = search.lower()
			tasks = [t for t in tasks if search_lower in t.get('title', '').lower() or
					search_lower in t.get('description', '').lower()]
		return [Task(**task) for task in tasks]

# Include the router in the main app
app.include_router(api_router)

# Mejor parseo de CORS_ORIGINS (quita entradas vacías y usa default localhost:3000)
origins_env = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
_origins = [o.strip() for o in origins_env.split(',') if o.strip()]
if '*' in _origins or origins_env.strip() == '*':
	allow_origins = ["*"]
else:
	allow_origins = _origins

app.add_middleware(
	CORSMiddleware,
	allow_credentials=True,
	allow_origins=allow_origins,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Intento de inicializar firebase en startup si el servicio lo soporta
@app.on_event("startup")
async def _initialize_services():
	try:
		if firebase_available:
			init_fn = None
			for name in ("initialize_app", "init", "start"):
				if hasattr(firebase_service, name):
					init_fn = getattr(firebase_service, name)
					break
			if init_fn:
				result = init_fn()
				if hasattr(result, "__await__"):
					await result
				logger.info("Firebase service initialized successfully")
	except Exception as e:
		logger.exception("Error initializing services on startup: %s", e)

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8001)