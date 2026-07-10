from functools import lru_cache
from pydantic_settings import BaseSettings




class Settings(BaseSettings):
    APP_NAME: str = "Water CRM"
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REDIS_URL: str


@lru_cache()
def get_settings() -> Settings:
    return Settings()