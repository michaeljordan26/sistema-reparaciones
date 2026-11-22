"""Punto de entrada del Microservicio 1: Usuarios y Autenticación."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auditoria import AuditoriaMiddleware
from app.core.config import settings
from app.routers import auth, tecnicos, usuarios

app = FastAPI(
    title="MS1 - Usuarios y Autenticación",
    description="Microservicio del taller de reparación: login JWT, usuarios, roles y técnicos.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Auditoría: cada operación que modifica datos se reporta a ms-reportes (8007)
app.add_middleware(AuditoriaMiddleware, servicio=settings.SERVICE_NAME, clave=settings.JWT_SECRET_KEY,
                   algoritmo=settings.JWT_ALGORITHM)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(tecnicos.router)


@app.get("/health", tags=["Salud"], summary="Comprobar que el servicio está vivo")
def health():
    return {"servicio": settings.SERVICE_NAME, "estado": "ok"}
