# Kubernetes-SD

Proyecto ejemplo: backend en FastAPI + Firebase (autenticación) y frontend en React (CRA + Tailwind).

## Requisitos
- Python 3.10+ (recomendado)
- Node.js 16+ y Yarn (o npm)
- Credenciales de Firebase (archivo JSON) para el admin SDK

## Estructura relevante
- Backend: [backend/server.py](backend/server.py), [backend/firebase_service.py](backend/firebase_service.py), [backend/auth_middleware.py](backend/auth_middleware.py)
- Frontend: [frontend/package.json](frontend/package.json), [frontend/src/contexts/AuthContext.js](frontend/src/contexts/AuthContext.js), [frontend/src/App.js](frontend/src/App.js)

## Configuración

1. Firebase
   - Coloca el archivo de credenciales del servicio en `backend/kubernetes-sd.json` (ruta usada por el admin SDK).
   - Si no se proporciona, el servidor arrancará en modo "mock" (ver `firebase_available` en [backend/server.py](backend/server.py)).

2. Variables de entorno
   - Backend: crea `backend/.env` con (ejemplo):
     - CORS_ORIGINS=http://localhost:3000
   - Frontend: crea `frontend/.env` con (ejemplo):
     - REACT_APP_BACKEND_URL=http://localhost:8001
     - REACT_APP_POSTHOG_KEY=  (opcional)

## Instalación y ejecución

Backend (FastAPI)
```bash
# Desde la raíz del repo
cd backend

# Crear y activar entorno virtual (example con venv)
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix / macOS
# source .venv/bin/activate

pip install -r requirements.txt

# Opción 1: ejecutar con uvicorn (recomendado para desarrollo)
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Opción 2: ejecutar directamente (server.py tiene guardia __main__)
python server.py
```

- El endpoint base: http://localhost:8001/api
- Ruta de comprobación de estado: http://localhost:8001/api/health
- Autenticación: las rutas protegidas usan el header `Authorization: Bearer <ID_TOKEN>` (ver [`get_current_user`](backend/auth_middleware.py)).

Frontend (React)
```bash
cd frontend

# Usando yarn (recomendado según package.json)
yarn install
yarn start

# O con npm
npm install
npm run start
```

- Asegúrate de que `REACT_APP_BACKEND_URL` en `frontend/.env` apunte a tu backend (por defecto http://localhost:8001). El cliente añade el token a las peticiones (ver [AuthContext.js](frontend/src/contexts/AuthContext.js)).