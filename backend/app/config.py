from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # DeepSeek LLM
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # Simulation defaults
    LLM_ENABLED: bool = False  # master switch to enable LLM features
    LLM_BUDGET_MAX: int = 50
    LLM_BUDGET_REPLENISH: float = 0.5

    class Config:
        env_file = ".env"


settings = Settings()
