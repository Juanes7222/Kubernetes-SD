from fastapi import FastAPI
from routers import logs

app = FastAPI(title="Logs Service")

app.include_router(logs.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "logs_service"}
