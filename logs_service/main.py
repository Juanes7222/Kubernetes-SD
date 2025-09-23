from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging_config import get_logger, request_log
from routers import logs
import time

logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Logs Service: %s version=%s", settings.PROJECT_NAME, settings.VERSION)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    has_auth = bool(request.headers.get("authorization"))
    request_log(request.method, request.url.path, response.status_code, process_time, auth=has_auth, name=__name__)
    return response

app.include_router(logs.router, prefix="/api/logs")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "logs"}