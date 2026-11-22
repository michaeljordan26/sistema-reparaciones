"""Configuración del microservicio. Los valores se leen del archivo .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "ms-reparaciones"
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost:5173"
    USUARIOS_URL: str = "http://127.0.0.1:8001"
    ORDENES_URL: str = "http://127.0.0.1:8003"
    INVENTARIO_URL: str = "http://127.0.0.1:8005"
    GARANTIA_DIAS_DEFECTO: int = 90
    HTTP_TIMEOUT: float = 8.0


settings = Settings()
