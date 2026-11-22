"""Punto de entrada del Microservicio 7: Reportes, notificaciones y auditoría."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import reportes

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="MS7 - Reportes, notificaciones y auditoría",
    description=("Recibe la auditoría de los otros 6 microservicios, genera las notificaciones al cliente "
                 "(envío simulado) y reúne los reportes del taller.\n\n"
                 "**Para probar:** obtén un token en http://127.0.0.1:8001/docs y pégalo en Authorize."),
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(reportes.router)


@app.get("/health", tags=["Salud"])
def health():
    return {"servicio": settings.SERVICE_NAME, "estado": "ok"}
