from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database settings
    DB_HOST: str = "10.0.0.131"
    DB_PORT: str = "30432"
    DB_NAME: str = "learntogrow_dev"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "admin@123"

    # Ollama settings
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "granite4.1:3b"
    OLLAMA_TIMEOUT: int = 300
    OLLAMA_GENERATION_WORKERS: int = 15
    OLLAMA_QUALITY_MODE: str = "reviewed"
    OLLAMA_CANDIDATE_COUNT: int = 1
    OLLAMA_MAX_REPAIR_ATTEMPTS: int = 0
    OLLAMA_MIN_REVIEW_SCORE: float = 0.75
    PARENT_ASSISTANT_MODEL: str = "gemma4:e4b"
    PARENT_ASSISTANT_TIMEOUT: int = 120

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
