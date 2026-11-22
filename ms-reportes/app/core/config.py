"""Configuración del microservicio. Los valores se leen del archivo .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "ms-reportes"
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost:5173"
    CLIENTES_URL: str = "http://127.0.0.1:8002"
    ORDENES_URL: str = "http://127.0.0.1:8003"
    REPARACIONES_URL: str = "http://127.0.0.1:8004"
    INVENTARIO_URL: str = "http://127.0.0.1:8005"
    FACTURACION_URL: str = "http://127.0.0.1:8006"
    HTTP_TIMEOUT: float = 6.0


settings = Settings()
