"""Comunicación HTTP con los otros microservicios.
Se reenvía el token del usuario: cada servicio vuelve a comprobar los permisos."""
import httpx
from fastapi import HTTPException, status

from app.core.config import settings


def _get(url: str, token: str, servicio: str) -> dict | None:
    """Devuelve el JSON, None si es 404, o lanza 503 si el servicio no responde."""
    try:
        r = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=settings.HTTP_TIMEOUT)
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            f"El servicio de {servicio} no está disponible. ¿Está encendido?")
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise HTTPException(r.status_code, f"El servicio de {servicio} rechazó el acceso")
    if r.status_code >= 400:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Error del servicio de {servicio}: {r.status_code}")
    return r.json()


def obtener_equipo(id_equipo: int, token: str) -> dict | None:
    """GET ms-clientes /equipos/{id} -> equipo con su cliente."""
    return _get(f"{settings.CLIENTES_URL}/equipos/{id_equipo}", token, "clientes")


def obtener_tecnico(id_tecnico: int, token: str) -> dict | None:
    """GET ms-usuarios /tecnicos/{id} -> técnico con su usuario."""
    return _get(f"{settings.USUARIOS_URL}/tecnicos/{id_tecnico}", token, "usuarios")


def saldo_pendiente(id_orden: int, token: str) -> float | None:
    """GET ms-facturacion /ordenes/{id}/saldo. None si el servicio aún no está configurado."""
    if not settings.FACTURACION_URL:
        return None
    datos = _get(f"{settings.FACTURACION_URL}/ordenes/{id_orden}/saldo", token, "facturación")
    return float(datos["saldo_pendiente"]) if datos else 0.0


def estado_presupuesto(id_orden: int, token: str) -> str | None:
    """GET ms-facturacion /ordenes/{id}/presupuesto -> 'PENDIENTE' | 'APROBADO' | 'RECHAZADO'.
    Devuelve 'SIN_VERIFICAR' si facturación no está configurada y None si la orden no tiene presupuesto."""
    if not settings.FACTURACION_URL:
        return "SIN_VERIFICAR"
    datos = _get(f"{settings.FACTURACION_URL}/ordenes/{id_orden}/presupuesto", token, "facturación")
    return datos["estado"] if datos else None
