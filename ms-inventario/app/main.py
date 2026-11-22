"""Punto de entrada del Microservicio 5: Inventario y repuestos."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auditoria import AuditoriaMiddleware
from app.core.config import settings
from app.routers import inventario

app = FastAPI(
    title="MS5 - Inventario y repuestos",
    description=("Repuestos, existencias y kardex. El stock nunca puede quedar negativo.\n\n"
                 "Las salidas consultan ms-ordenes (8003) para verificar que la orden está EN_REPARACION.\n\n"
                 "**Para probar:** obtén un token en http://127.0.0.1:8001/docs y pégalo en Authorize."),
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# Auditoría: cada operación que modifica datos se reporta a ms-reportes (8007)
app.add_middleware(AuditoriaMiddleware, servicio=settings.SERVICE_NAME, clave=settings.JWT_SECRET_KEY,
                   algoritmo=settings.JWT_ALGORITHM)
app.include_router(inventario.router)


@app.get("/health", tags=["Salud"])
def health():
    return {"servicio": settings.SERVICE_NAME, "estado": "ok"}
