"""Configuración del microservicio. Los valores se leen del archivo .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "ms-ordenes"
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost:5173"
    USUARIOS_URL: str = "http://127.0.0.1:8001"
    CLIENTES_URL: str = "http://127.0.0.1:8002"
    FACTURACION_URL: str = ""          # Vacío = todavía no se verifica el pago
    HTTP_TIMEOUT: float = 5.0


settings = Settings()
