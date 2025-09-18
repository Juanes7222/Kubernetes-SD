from fastapi import FastAPI
from routers import tasks, lists

# Atributos de la aplicación
app = FastAPI(
    title="Kubernets-SD",
    description="Monolito base para elaborar el trabajo de Sistemas Distribuidos"
)

# Routers
app.include_router(lists.router)
app.include_router(tasks.router)
