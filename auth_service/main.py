from fastapi import FastAPI, Depends, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging_config import get_logger, request_log
from routers import auth
from starlette.responses import JSONResponse
import time

logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Auth Service: %s version=%s", settings.PROJECT_NAME, settings.VERSION)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled exception during request %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse({"detail": "Internal server error"}, status_code=500)
    process_time = time.time() - start_time
    has_auth = bool(request.headers.get("authorization"))
    request_log(request.method, request.url.path, response.status_code, process_time, auth=has_auth, name=__name__)
    return response

# Routers
app.include_router(auth.router, prefix="/api/auth")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth"}