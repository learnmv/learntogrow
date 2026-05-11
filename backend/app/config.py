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
    OLLAMA_MODEL: str = "deepseek-r1:1.5b"
    OLLAMA_TIMEOUT: int = 300
    PARENT_ASSISTANT_MODEL: str = "gemma4:e4b"
    PARENT_ASSISTANT_TIMEOUT: int = 120

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
