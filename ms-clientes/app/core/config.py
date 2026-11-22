"""Configuración del microservicio. Los valores se leen del archivo .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "ms-clientes"
    DATABASE_URL: str
    JWT_SECRET_KEY: str          # La misma de ms-usuarios
    JWT_ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost:5173"


settings = Settings()
