from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LLM_API_URL: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "ollama"
    LLM_MODEL: str = "llama3:8b-instruct-q3_K_m"
    LLM_TEMPERATURE: float = 0.0
    LLM_SEED: int = 42

    SQLITE_DB: str = "freelancers.db"
    SQLITE_TABLE: str = "freelancers"

    CSV_FILE_PATH: str = "data/freelancer_earnings_bd.csv"

    CACHE_DIR: str = ".cache"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
