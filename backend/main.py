from fastapi import FastAPI, Request
from routers import tasks, auth, logs, services
from starlette.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging_config import get_logger, request_log, write
from starlette.responses import JSONResponse
import time

logger = get_logger(__name__)

# Create the main app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting backend: %s version=%s", settings.PROJECT_NAME, settings.VERSION)
    # Inicializar service registry
    from services.service_registry import service_registry
    await service_registry.initialize()
    
    # Auto-registrar el backend API
    try:
        await service_registry.register_service({
            "name": "todo-backend-api",
            "host": "localhost",
            "port": 8001,
            "protocol": "http",
            "health_check_url": "http://localhost:8001/health",
            "tags": ["api", "backend", "todo", "fastapi"]
        })
        logger.info("Backend API auto-registered in service registry")
    except Exception as e:
        logger.warning("Failed to auto-register backend API: %s", e)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Log unhandled exceptions
        logger.exception("Unhandled exception during request %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse({"detail": "Internal server error"}, status_code=500)
    process_time = time.time() - start_time
    # Mask authorization presence (don't log token contents)
    has_auth = bool(request.headers.get("authorization"))
    request_log(request.method, request.url.path, response.status_code, process_time, auth=has_auth, name=__name__)
    return response

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(services.router, prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    # Emit a root hit log so we can validate logging from requests
    write("info", "root_ping", name=__name__)
    return {"message": f"{settings.PROJECT_NAME} is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "version": settings.VERSION, "api": "ready"}
