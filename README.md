# Kubernetes-SD

Proyecto académico para la asignatura de Sistemas Distribuidos, orientado al desarrollo de un sistema monolítico para la gestión de tareas (To-Do) colaborativo. El backend fue desarrollado con FastAPI, integrando los servicios de Cloud Firestore para la base de datos y Firebase Authentication para la gestión de usuarios, capaz de soportar tanto las credenciales de Google como la autenticación mediante correo electrónico y contraseña. El frontend fue implementado utilizando React (CRA + Tailwind) para la interfaz de usuario.

## Requisitos

### backend
- Python 3.10+
- FastAPI
- Uvicorn
- Firebase Admin SDK
- Credenciales de Firebase (archivo JSON)
- Dependencias adicionales definidas en requirements.txt

### frontend
- Node.js 16+
- Yarn o npm
- React
- Tailwind CSS
- Dependencias adicionales definidas en package.json

## Estructura relevante
El proyecto se divide en dos módulos principales:
- **backend**: Concentra la lógica del servidor, integra los servicios de Firebase y define los endpoints.
- **frontend**: Contiene la interfaz de usuario y se conecta con el backend.

Estructura de carpetas y archivos más relevantes:

```plaintext
Kubernetes-SD/
├── backend/
│   ├── auth_middleware.py
│   ├── firebase_service.py
│   ├── requirements.txt
│   └── server.py
│
└── frontend/
    ├── src/
    │   ├── App.js
    │   ├── components/Auth/
    │   │   ├── LoginForms.js
    │   │   └── SignupForm.js
    │   ├── contexts/
    │   │   └── AuthContext.js
    │   └── lib/
    │       └── utils.js
    ├── package-lock.json
    └── package.json
```
## Configuración Adicional
1. Firebase
   - Coloca el archivo de credenciales del servicio en `backend/kubernetes-sd.json` (ruta usada por el admin SDK).
   - Si no se proporciona, el servidor arrancará en modo "mock" (ver `firebase_available` en [backend/server.py](backend/server.py)).

2. Variables de entorno
   - Backend: crea `backend/.env` con, por ejemplo:
     - CORS_ORIGINS=http://localhost:3000
   - Frontend: crea `frontend/.env` con, por ejemplo:
     - REACT_APP_BACKEND_URL=http://localhost:8001
     - REACT_APP_POSTHOG_KEY=  (opcional)

## Instalación y ejecución
### Backend (FastAPI)
```bash
# Desde la raíz del proyecto
cd backend

# Crea y activa entorno virtual (en este ejemplo se nombra como .venv)
python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # Unix / macOS
   source .venv/bin/activate

# Instala las dependencias adicionales
pip install -r requirements.txt

# Inicia el servidor
   # Opción 1: ejecuta con uvicorn (recomendado)
   uvicorn server:app --reload --host 0.0.0.0 --port 8001
   
   # Opción 2: ejecuta directamente (tiene guardia __main__)
   python server.py
```

- Endpoint base: http://localhost:8001/api
- Ruta de comprobación de estado: http://localhost:8001/api/health
- **Autenticación:** las rutas protegidas usan el header `Authorization: Bearer <ID_TOKEN>` (ver [`get_current_user`](backend/auth_middleware.py)).

### Frontend (React)
```bash
# Desde la raíz del proyecto
cd frontend

# Instala las dependencias requeridas
   # Opción 1: Usa yarn (recomendado según package.json)
   yarn install
   yarn start
   
   # Opción 2: Usa npm
   npm install
   npm run start
```

- Asegúrese de que `REACT_APP_BACKEND_URL` en `frontend/.env` apunte a tu backend (por defecto http://localhost:8001).
- El cliente añade el token a las peticiones (ver [AuthContext.js](frontend/src/contexts/AuthContext.js)).
