"""Comunicación HTTP con ms-ordenes y ms-inventario (se reenvía el token del usuario)."""
import httpx
from fastapi import HTTPException, status

from app.core.config import settings


def _llamar(metodo: str, url: str, token: str, servicio: str, json: dict | None = None) -> dict | None:
    try:
        r = httpx.request(metodo, url, json=json, headers={"Authorization": f"Bearer {token}"},
                          timeout=settings.HTTP_TIMEOUT)
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            f"El servicio de {servicio} no está disponible. ¿Está encendido?")
    if r.status_code == 404 and metodo == "GET":
        return None
    if r.status_code >= 400:
        try:
            detalle = r.json().get("detail")
        except ValueError:
            detalle = r.text
        if isinstance(detalle, list):
            detalle = "; ".join(str(d.get("msg")) for d in detalle)
        codigo = r.status_code if r.status_code < 500 else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(codigo, f"[{servicio}] {detalle}")
    return r.json()


def obtener_orden(id_orden: int, token: str) -> dict | None:
    return _llamar("GET", f"{settings.ORDENES_URL}/ordenes/{id_orden}", token, "órdenes")


def cambiar_estado_orden(id_orden: int, estado: str, observacion: str, token: str) -> dict:
    return _llamar("PATCH", f"{settings.ORDENES_URL}/ordenes/{id_orden}/estado", token, "órdenes",
                   json={"estado": estado, "observacion": observacion[:500]})


def obtener_repuesto(id_repuesto: int, token: str) -> dict | None:
    return _llamar("GET", f"{settings.INVENTARIO_URL}/repuestos/{id_repuesto}", token, "inventario")


def consumo_orden(id_orden: int, token: str) -> dict:
    """Repuestos REALMENTE usados en la orden (salidas menos devoluciones) según ms-inventario."""
    return _llamar("GET", f"{settings.INVENTARIO_URL}/ordenes/{id_orden}/consumo", token, "inventario") \
        or {"lineas": [], "total_materiales": 0}
