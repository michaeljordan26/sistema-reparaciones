"""Configuración del microservicio. Los valores se leen del archivo .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "ms-inventario"
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost:5173"
    ORDENES_URL: str = "http://127.0.0.1:8003"   # Vacío = no se verifica la orden
    HTTP_TIMEOUT: float = 5.0


settings = Settings()
