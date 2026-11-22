"""Punto de entrada del Microservicio 6: Presupuestos, facturación y pagos."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auditoria import AuditoriaMiddleware
from app.core.config import settings
from app.routers import facturacion

app = FastAPI(
    title="MS6 - Presupuestos, facturación y pagos",
    description=("Presupuestos con materiales y mano de obra, aprobación del cliente, facturas, pagos, abonos "
                 "y saldos. ms-ordenes consulta aquí el saldo antes de permitir la entrega.\n\n"
                 "Depende de ms-ordenes (8003) e ms-inventario (8005).\n\n"
                 "**Para probar:** obtén un token en http://127.0.0.1:8001/docs y pégalo en Authorize."),
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# Auditoría: cada operación que modifica datos se reporta a ms-reportes (8007)
app.add_middleware(AuditoriaMiddleware, servicio=settings.SERVICE_NAME, clave=settings.JWT_SECRET_KEY,
                   algoritmo=settings.JWT_ALGORITHM)
app.include_router(facturacion.router)


@app.get("/health", tags=["Salud"])
def health():
    return {"servicio": settings.SERVICE_NAME, "estado": "ok"}
