from fastapi import FastAPI
from routers import tasks, auth
from starlette.middleware.cors import CORSMiddleware
from core.config import settings

# Create the main app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")

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
    return {"message": f"{settings.PROJECT_NAME} is running!"}
