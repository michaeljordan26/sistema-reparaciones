"""Lecturas a los otros microservicios. Todas son GET: ms-reportes no modifica datos ajenos."""
import httpx
from fastapi import HTTPException, status

from app.core.config import settings


class ServicioNoDisponible(Exception):
    pass


def _get(url: str, token: str, servicio: str, params: dict | None = None):
    try:
        r = httpx.get(url, params=params, headers={"Authorization": f"Bearer {token}"},
                      timeout=settings.HTTP_TIMEOUT)
    except httpx.HTTPError:
        raise ServicioNoDisponible(f"El servicio de {servicio} no está disponible")
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise HTTPException(r.status_code, f"[{servicio}] acceso denegado")
    if r.status_code >= 400:
        raise ServicioNoDisponible(f"El servicio de {servicio} respondió {r.status_code}")
    return r.json()


def ordenes(token: str) -> list[dict]:
    return _get(f"{settings.ORDENES_URL}/ordenes", token, "órdenes") or []


def orden(id_orden: int, token: str) -> dict | None:
    return _get(f"{settings.ORDENES_URL}/ordenes/{id_orden}", token, "órdenes")


def equipo(id_equipo: int, token: str) -> dict | None:
    """Incluye el cliente (nombre, correo, teléfono)."""
    return _get(f"{settings.CLIENTES_URL}/equipos/{id_equipo}", token, "clientes")


def ingresos(token: str, desde: str | None, hasta: str | None) -> dict:
    params = {k: v for k, v in {"desde": desde, "hasta": hasta}.items() if v}
    return _get(f"{settings.FACTURACION_URL}/reportes/ingresos", token, "facturación", params)


def cartera(token: str) -> dict:
    return _get(f"{settings.FACTURACION_URL}/reportes/cartera", token, "facturación")


def repuestos(token: str) -> list[dict]:
    return _get(f"{settings.INVENTARIO_URL}/repuestos", token, "inventario") or []


def garantias_vigentes(token: str) -> list[dict]:
    return _get(f"{settings.REPARACIONES_URL}/garantias", token, "reparaciones", {"estado": "VIGENTE"}) or []


__all__ = ["ServicioNoDisponible", "HTTPException", "status"]
