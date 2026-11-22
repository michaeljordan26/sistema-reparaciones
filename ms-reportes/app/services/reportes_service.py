"""Reportes: reúne datos de los otros microservicios usando el token del usuario que consulta
(así cada servicio sigue aplicando sus propios permisos)."""
from collections import Counter
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.clients import externos
from app.schemas.reportes import PanelOut, Seccion
from app.core.tiempo import hoy as hoy_colombia
from app.services import auditoria_service

PENDIENTES = ["RECIBIDO", "EN_DIAGNOSTICO", "ESPERANDO_APROBACION", "EN_REPARACION", "LISTO_ENTREGA"]
PRIORIDAD = {"URGENTE": 0, "ALTA": 1, "MEDIA": 2, "BAJA": 3}


def _fecha(texto: str | None) -> datetime | None:
    return datetime.fromisoformat(texto) if texto else None


def ordenes(token: str) -> dict:
    lista = externos.ordenes(token)
    por_estado = Counter(o["estado_actual"] for o in lista)
    pendientes = sorted((o for o in lista if o["estado_actual"] in PENDIENTES),
                        key=lambda o: (PRIORIDAD.get(o["prioridad"], 9), o["fecha_recepcion"] or ""))
    carga = Counter(o["asignacion_activa"]["nombre_tecnico"] for o in pendientes if o.get("asignacion_activa"))
    tiempos = [(_fecha(o["fecha_cierre"]) - _fecha(o["fecha_recepcion"])).total_seconds() / 86400
               for o in lista if o["estado_actual"] == "ENTREGADO" and o["fecha_cierre"] and o["fecha_recepcion"]]
    return {
        "total": len(lista),
        "pendientes": len(pendientes),
        "finalizadas": por_estado.get("ENTREGADO", 0) + por_estado.get("CANCELADO", 0),
        "por_estado": dict(por_estado),
        "carga_por_tecnico": dict(carga),
        "sin_tecnico": sum(1 for o in pendientes if not o.get("asignacion_activa")),
        "dias_promedio_hasta_entrega": round(sum(tiempos) / len(tiempos), 2) if tiempos else None,
        "lista_pendientes": [{"id_orden": o["id_orden"], "codigo": o["codigo"], "estado": o["estado_actual"],
                              "prioridad": o["prioridad"], "fecha_recepcion": o["fecha_recepcion"],
                              "tecnico": (o.get("asignacion_activa") or {}).get("nombre_tecnico")}
                             for o in pendientes],
    }


def finanzas(token: str, desde: date | None = None, hasta: date | None = None) -> dict:
    ing = externos.ingresos(token, desde.isoformat() if desde else None, hasta.isoformat() if hasta else None)
    car = externos.cartera(token)
    return {"ingresos": ing, "cartera": car}


def inventario(token: str) -> dict:
    reps = externos.repuestos(token)
    bajos = [r for r in reps if r["stock_bajo"]]
    return {
        "total_repuestos": len(reps),
        "unidades_en_stock": sum(r["stock_actual"] for r in reps),
        "valor_inventario_costo": round(sum(r["stock_actual"] * r["precio_costo"] for r in reps), 2),
        "stock_bajo": [{"id_repuesto": r["id_repuesto"], "codigo": r["codigo"], "nombre": r["nombre"],
                        "stock_actual": r["stock_actual"], "stock_minimo": r["stock_minimo"]} for r in bajos],
    }


def garantias(token: str) -> dict:
    vigentes = externos.garantias_vigentes(token)
    hoy = hoy_colombia()
    por_vencer = [g for g in vigentes if (date.fromisoformat(g["fecha_fin"]) - hoy).days <= 15]
    reclamaciones_abiertas = sum(1 for g in vigentes for r in g.get("reclamaciones", []) if r["estado"] == "ABIERTA")
    return {"vigentes": len(vigentes), "por_vencer_15_dias": len(por_vencer),
            "reclamaciones_abiertas": reclamaciones_abiertas}


def _seccion(funcion, *args) -> Seccion:
    try:
        return Seccion(disponible=True, datos=funcion(*args))
    except externos.ServicioNoDisponible as e:
        return Seccion(disponible=False, error=str(e))
    except HTTPException as e:
        return Seccion(disponible=False, error=str(e.detail))


def panel(db: Session, token: str) -> PanelOut:
    """Tablero del administrador. Si un servicio está caído, solo esa sección queda sin datos."""
    return PanelOut(
        generado=datetime.now(timezone.utc),
        ordenes=_seccion(ordenes, token),
        finanzas=_seccion(finanzas, token),
        inventario=_seccion(inventario, token),
        garantias=_seccion(garantias, token),
        auditoria=_seccion(lambda: auditoria_service.resumen(db, 24)),
    )
