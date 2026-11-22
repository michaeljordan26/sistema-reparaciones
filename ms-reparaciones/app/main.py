"""Punto de entrada del Microservicio 4: Diagnósticos, reparaciones y garantías."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auditoria import AuditoriaMiddleware
from app.core.config import settings
from app.routers import reparaciones

app = FastAPI(
    title="MS4 - Diagnósticos, reparaciones y garantías",
    description=("Trabajo técnico sobre la orden. Coordina ms-ordenes (8003), ms-inventario (8005) "
                 "y ms-usuarios (8001), que deben estar encendidos.\n\n"
                 "**Para probar:** obtén un token en http://127.0.0.1:8001/docs y pégalo en Authorize."),
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# Auditoría: cada operación que modifica datos se reporta a ms-reportes (8007)
app.add_middleware(AuditoriaMiddleware, servicio=settings.SERVICE_NAME, clave=settings.JWT_SECRET_KEY,
                   algoritmo=settings.JWT_ALGORITHM)
app.include_router(reparaciones.router)


@app.get("/health", tags=["Salud"])
def health():
    return {"servicio": settings.SERVICE_NAME, "estado": "ok"}
