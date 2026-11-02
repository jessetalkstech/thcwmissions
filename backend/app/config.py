from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str
    OLLAMA_API_BASE: str
    OLLAMA_MODEL_NAME: str
    SECRET_KEY: str
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: List[str] = ["*"]

    class Config:
        env_file = ".env"

settings = Settings()
