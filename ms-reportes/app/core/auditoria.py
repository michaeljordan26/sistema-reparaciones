"""Middleware de AUDITORÍA (este mismo archivo está en todos los microservicios).

Cada vez que llega una operación que MODIFICA datos (POST, PUT, PATCH, DELETE), este
middleware arma un evento con: servicio, ruta, usuario, roles, código de respuesta,
id del recurso afectado y duración, y lo envía a ms-reportes (POST /auditoria/eventos).

- El envío se hace en un hilo aparte: el usuario NO espera a la auditoría.
- Si ms-reportes está apagado, la operación funciona igual (solo se escribe un aviso en la consola).
- Nunca se envían cuerpos de petición (podrían traer contraseñas).
- El evento va firmado con un token de servicio (rol SERVICIO) usando la misma JWT_SECRET_KEY,
  para que nadie pueda inventar registros de auditoría.

Configuración: variable de entorno AUDITORIA_URL (por defecto http://127.0.0.1:8007).
Déjala vacía para desactivar la auditoría.
"""
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

log = logging.getLogger("auditoria")
METODOS_AUDITADOS = {"POST", "PUT", "PATCH", "DELETE"}
MAX_CUERPO = 200_000   # bytes de respuesta que se inspeccionan para buscar el id creado


def enviar_evento(url: str, token: str, evento: dict) -> None:
    try:
        httpx.post(f"{url}/auditoria/eventos", json=evento,
                   headers={"Authorization": f"Bearer {token}"}, timeout=3)
    except httpx.HTTPError as e:
        log.warning("No se pudo registrar la auditoría (%s): %s", evento.get("ruta"), e)


def despachar(url: str, token: str, evento: dict) -> None:
    threading.Thread(target=enviar_evento, args=(url, token, evento), daemon=True).start()


class AuditoriaMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, servicio: str, clave: str, algoritmo: str = "HS256"):
        super().__init__(app)
        self.servicio = servicio
        self.clave = clave
        self.algoritmo = algoritmo

    @staticmethod
    def _url() -> str:
        return os.getenv("AUDITORIA_URL", "http://127.0.0.1:8007").rstrip("/")

    @staticmethod
    def _habilitada() -> bool:
        # Durante pytest no se audita (salvo que la prueba lo pida explícitamente)
        if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("AUDITORIA_EN_PRUEBAS") != "1":
            return False
        return bool(AuditoriaMiddleware._url())

    def _usuario(self, request) -> tuple[int | None, list[str]]:
        cabecera = request.headers.get("authorization", "")
        if not cabecera.lower().startswith("bearer "):
            return None, []
        try:
            datos = jwt.decode(cabecera[7:], self.clave, algorithms=[self.algoritmo])
            return int(datos["sub"]), list(datos.get("roles", []))
        except (jwt.PyJWTError, KeyError, ValueError):
            return None, []

    def _token_servicio(self) -> str:
        datos = {"sub": f"servicio:{self.servicio}", "roles": ["SERVICIO"],
                 "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
        return jwt.encode(datos, self.clave, algorithm=self.algoritmo)

    async def dispatch(self, request, call_next):
        if request.method not in METODOS_AUDITADOS or not self._habilitada():
            return await call_next(request)

        inicio = time.perf_counter()
        id_usuario, roles = self._usuario(request)
        response = await call_next(request)
        duracion = round((time.perf_counter() - inicio) * 1000)

        ruta_plantilla = getattr(request.scope.get("route"), "path", request.url.path)
        params = request.scope.get("path_params") or {}
        recurso_id = str(next(iter(params.values()))) if params else None

        # Para las creaciones (POST) se lee la respuesta para saber qué id se creó
        if response.status_code < 300 and "application/json" in response.headers.get("content-type", ""):
            cuerpo = b"".join([trozo async for trozo in response.body_iterator])
            response = Response(content=cuerpo, status_code=response.status_code,
                                headers=dict(response.headers), media_type=response.media_type)
            if len(cuerpo) < MAX_CUERPO:
                try:
                    datos = json.loads(cuerpo)
                    if isinstance(datos, dict):
                        if request.method == "POST":
                            clave_id = next((k for k in datos if k.startswith("id_")), None)
                            if clave_id:
                                recurso_id = str(datos[clave_id])
                        if "access_token" in datos and id_usuario is None:   # inicio de sesión exitoso
                            pl = jwt.decode(datos["access_token"], self.clave, algorithms=[self.algoritmo])
                            id_usuario, roles = int(pl["sub"]), list(pl.get("roles", []))
                except (ValueError, jwt.PyJWTError, KeyError):
                    pass

        evento = {
            "servicio": self.servicio, "metodo": request.method, "ruta": request.url.path,
            "ruta_plantilla": ruta_plantilla, "recurso_id": recurso_id, "codigo_estado": response.status_code,
            "id_usuario": id_usuario, "roles": roles, "duracion_ms": duracion,
            "ip": request.client.host if request.client else None,
        }
        despachar(self._url(), self._token_servicio(), evento)
        return response
