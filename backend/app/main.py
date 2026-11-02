from fastapi import FastAPI
from backend.app.routes import router

app = FastAPI(title="thcwmissions")

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
