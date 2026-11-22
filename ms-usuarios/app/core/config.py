"""Configuración del microservicio. Los valores se leen del archivo .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "ms-usuarios"
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    ADMIN_EMAIL: str = "admin@taller.com"
    ADMIN_PASSWORD: str = "Admin123*"
    CORS_ORIGINS: str = "http://localhost:5173"


settings = Settings()
