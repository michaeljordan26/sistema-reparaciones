"""Punto de entrada del Microservicio 2: Clientes y Equipos."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auditoria import AuditoriaMiddleware
from app.core.config import settings
from app.routers import clientes, equipos

app = FastAPI(
    title="MS2 - Clientes y Equipos",
    description=("Registro de clientes del taller y de los equipos que entregan para servicio.\n\n"
                 "**Para probar:** obtén un token en ms-usuarios (http://127.0.0.1:8001/docs) "
                 "o usa el botón Authorize con un usuario de prueba."),
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# Auditoría: cada operación que modifica datos se reporta a ms-reportes (8007)
app.add_middleware(AuditoriaMiddleware, servicio=settings.SERVICE_NAME, clave=settings.JWT_SECRET_KEY,
                   algoritmo=settings.JWT_ALGORITHM)

app.include_router(clientes.router)
app.include_router(equipos.router)


@app.get("/health", tags=["Salud"])
def health():
    return {"servicio": settings.SERVICE_NAME, "estado": "ok"}
