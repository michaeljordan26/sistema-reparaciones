"""Comunicación HTTP con ms-ordenes para validar la orden antes de sacar repuestos."""
import httpx
from fastapi import HTTPException, status

from app.core.config import settings


def obtener_orden(id_orden: int, token: str) -> dict | None:
    """GET ms-ordenes /ordenes/{id}. Devuelve {} si la verificación está desactivada."""
    if not settings.ORDENES_URL:
        return {}
    try:
        r = httpx.get(f"{settings.ORDENES_URL}/ordenes/{id_orden}",
                      headers={"Authorization": f"Bearer {token}"}, timeout=settings.HTTP_TIMEOUT)
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "El servicio de órdenes no está disponible. ¿Está encendido?")
    if r.status_code == 404:
        return None
    if r.status_code >= 400:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Error del servicio de órdenes: {r.status_code}")
    return r.json()
