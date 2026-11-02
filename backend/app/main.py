from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="thcwmissions")

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
