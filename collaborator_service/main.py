from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import collaborators
from core.logging_config import get_logger
from core import config

logger = get_logger(__name__)

app = FastAPI(
    title=config.SERVICE_NAME,
    version=config.VERSION,
    description=config.DESCRIPTION
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(collaborators.router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": config.SERVICE_NAME,
        "version": config.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
