from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # LLM
    LLM_PROVIDER: str = Field(default="groq")
    GROQ_API_KEY: Optional[str] = Field(default=None)
    LLM_MODEL: str = Field(default="llama-3.3-70b-versatile")
    LLM_TIMEOUT_SECONDS: int = Field(default=30, ge=1)
    LLM_MAX_RETRIES: int = Field(default=1, ge=0)

    # Pipeline
    MAX_CANDIDATES: int = Field(default=20, ge=1)
    MAX_RESULTS: int = Field(default=5, ge=1)
    DATA_CACHE_PATH: str = Field(default="data/processed/restaurants.parquet")

    # API
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000, ge=1, le=65535)
