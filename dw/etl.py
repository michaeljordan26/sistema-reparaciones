"""ETL del taller: de las 7 bases OLTP (microservicios) al Data Warehouse en estrella (db_dw).

    EXTRACT    lee las tablas de cada microservicio (solo lectura, SELECT)
    TRANSFORM  une los datos de bases distintas por sus ids, calcula indicadores
               (días hasta la entrega, saldo, margen) y arma dimensiones y hechos
    LOAD       recarga el Data Warehouse en UNA transacción: si algo falla, no queda a medias

Se puede ejecutar las veces que se quiera (carga completa):
    python etl.py
"""
import json
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text

import config

COL = ZoneInfo("America/Bogota")
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
         "Octubre", "Noviembre", "Diciembre"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
SIN_TECNICO = -1


# ====================================================================== EXTRACT
CONSULTAS = {
    "usuarios": {
        "tecnico": "SELECT t.id_tecnico, u.nombres || ' ' || u.apellidos AS nombre, t.especialidad, t.estado_laboral "
                   "FROM tecnico t JOIN usuario u ON u.id_usuario = t.id_usuario",
    },
    "clientes": {
        "cliente": "SELECT * FROM cliente",
        "equipo": "SELECT id_equipo, tipo_equipo, marca, modelo FROM equipo",
    },
    "ordenes": {
        "orden": "SELECT * FROM orden_trabajo",
        "asignacion": "SELECT id_orden, id_tecnico, estado_asignacion, fecha_asignacion FROM asignacion",
        "historial": "SELECT id_orden, estado_nuevo, fecha_cambio FROM historial_estado",
    },
    "reparaciones": {
        "reparacion": "SELECT id_orden, id_tecnico, resultado FROM reparacion",
        "usado": "SELECT u.*, r.id_orden, r.id_tecnico FROM repuesto_utilizado u "
                 "JOIN reparacion r ON r.id_reparacion = u.id_reparacion",
    },
    "inventario": {
        "repuesto": "SELECT * FROM repuesto",
    },
    "facturacion": {
        "presupuesto": "SELECT id_orden, total, estado FROM presupuesto WHERE estado <> 'ANULADO'",
        "factura": "SELECT id_factura, id_orden, total FROM factura WHERE NOT anulada",
        "pago": "SELECT p.*, f.id_orden FROM pago p JOIN factura f ON f.id_factura = p.id_factura "
                "WHERE NOT p.anulado AND NOT f.anulada",
    },
}


def extraer():
    datos = {}
    for servicio, consultas in CONSULTAS.items():
        motor = create_engine(config.ORIGENES[servicio])
        with motor.connect() as c:
            for nombre, sql in consultas.items():
                datos[nombre] = [dict(f._mapping) for f in c.execute(text(sql))]
        motor.dispose()
        print(f"  extraído  {servicio:13} " + ", ".join(f"{k}={len(datos[k])}" for k in consultas))
    return datos


# ====================================================================== TRANSFORM
def id_fecha(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        valor = valor.astimezone(COL).date()     # el día se cuenta en hora de Colombia
    return valor.year * 10000 + valor.month * 100 + valor.day


def construir_dim_fecha(fechas):
    validas = [f for f in fechas if f]
    inicio = min(validas)
    fin = max(max(validas), datetime.now(COL).date())
    filas, d = [], inicio
    while d <= fin:
        filas.append({"id_fecha": id_fecha(d), "fecha": d, "anio": d.year, "trimestre": (d.month - 1) // 3 + 1,
                      "mes": d.month, "nombre_mes": MESES[d.month - 1], "anio_mes": f"{d.year}-{d.month:02d}",
                      "dia": d.day, "dia_semana": d.isoweekday(), "nombre_dia": DIAS[d.weekday()],
                      "es_fin_semana": d.isoweekday() >= 6})
        d += timedelta(days=1)
    return filas


def transformar(d):
    dim_tecnico = [{"id_tecnico": SIN_TECNICO, "nombre": "Sin asignar", "especialidad": None,
                    "estado_laboral": "ACTIVO"}] + d["tecnico"]
    dim_cliente = [{"id_cliente": c["id_cliente"], "documento": f"{c['tipo_documento']} {c['numero_documento']}",
                    "nombre": f"{c['nombres']} {c['apellidos']}", "tiene_correo": bool(c["correo"]),
                    "fecha_registro": c["fecha_registro"].astimezone(COL).date(), "estado": c["estado"]}
                   for c in d["cliente"]]
    dim_equipo = d["equipo"]
    dim_repuesto = [{k: r[k] for k in ("id_repuesto", "codigo", "nombre", "categoria", "marca", "precio_costo",
                                       "precio_venta", "stock_actual", "stock_minimo")}
                    | {"stock_bajo": r["stock_actual"] <= r["stock_minimo"]} for r in d["repuesto"] if r["activo"]]
    costo = {r["id_repuesto"]: r["precio_costo"] for r in d["repuesto"]}

    # Índices para unir datos que vienen de bases distintas (por id de orden)
    tecnico_de = {}
    for a in sorted(d["asignacion"], key=lambda a: a["fecha_asignacion"]):
        tecnico_de[a["id_orden"]] = a["id_tecnico"]          # la última asignación es la que cuenta
    diagnostico_en = {h["id_orden"]: h["fecha_cambio"] for h in d["historial"]
                      if h["estado_nuevo"] == "ESPERANDO_APROBACION"}
    presupuesto = {p["id_orden"]: p for p in d["presupuesto"]}
    resultado = {r["id_orden"]: r["resultado"] for r in d["reparacion"]}
    facturado = defaultdict(Decimal)
    for f in d["factura"]:
        facturado[f["id_orden"]] += f["total"]
    pagado = defaultdict(Decimal)
    for p in d["pago"]:
        pagado[p["id_orden"]] += p["monto"]
    usados = defaultdict(int)
    for u in d["usado"]:
        usados[u["id_orden"]] += u["cantidad"]

    fact_orden = []
    for o in d["orden"]:
        oid, recibido, cierre = o["id_orden"], o["fecha_recepcion"], o["fecha_cierre"]
        p = presupuesto.get(oid)
        diag = diagnostico_en.get(oid)
        fact_orden.append({
            "id_orden": oid, "id_fecha_recepcion": id_fecha(recibido), "id_fecha_cierre": id_fecha(cierre),
            "id_cliente": o["id_cliente"], "id_equipo": o["id_equipo"],
            "id_tecnico": tecnico_de.get(oid, SIN_TECNICO), "estado": o["estado_actual"],
            "prioridad": o["prioridad"],
            "decision_presupuesto": p["estado"] if p and p["estado"] in ("APROBADO", "RECHAZADO") else None,
            "resultado_reparacion": resultado.get(oid),
            "abierta": o["estado_actual"] not in ("ENTREGADO", "CANCELADO"),
            "dias_hasta_cierre": round(Decimal((cierre - recibido).total_seconds() / 86400), 2) if cierre else None,
            "horas_hasta_diagnostico": round(Decimal((diag - recibido).total_seconds() / 3600), 2) if diag else None,
            "valor_presupuesto": p["total"] if p else 0, "valor_facturado": facturado[oid],
            "valor_pagado": pagado[oid], "saldo_pendiente": facturado[oid] - pagado[oid],
            "repuestos_usados": usados[oid]})

    cliente_de = {o["id_orden"]: o["id_cliente"] for o in d["orden"]}
    fact_pago = [{"id_pago": p["id_pago"], "id_fecha": id_fecha(p["fecha"]), "id_orden": p["id_orden"],
                  "id_cliente": cliente_de[p["id_orden"]], "metodo": p["metodo"], "tipo": p["tipo"],
                  "monto": p["monto"]} for p in d["pago"]]

    fact_repuesto = []
    for u in d["usado"]:
        venta = u["precio_unitario"] * u["cantidad"]
        coste = costo.get(u["id_repuesto"], Decimal(0)) * u["cantidad"]
        fact_repuesto.append({"id_repuesto_utilizado": u["id_repuesto_utilizado"], "id_fecha": id_fecha(u["fecha"]),
                              "id_orden": u["id_orden"], "id_repuesto": u["id_repuesto"],
                              "id_tecnico": u["id_tecnico"] or SIN_TECNICO, "cantidad": u["cantidad"],
                              "valor_venta": venta, "valor_costo": coste, "margen": venta - coste})

    a_dia = lambda v: v.astimezone(COL).date() if v else None
    fechas = ([a_dia(o["fecha_recepcion"]) for o in d["orden"]] + [a_dia(o["fecha_cierre"]) for o in d["orden"]]
              + [a_dia(p["fecha"]) for p in d["pago"]] + [a_dia(u["fecha"]) for u in d["usado"]]
              + [c["fecha_registro"] for c in dim_cliente])
    return {
        "dim_fecha": construir_dim_fecha(fechas), "dim_cliente": dim_cliente, "dim_equipo": dim_equipo,
        "dim_tecnico": dim_tecnico, "dim_repuesto": dim_repuesto,
        "fact_orden": fact_orden, "fact_pago": fact_pago, "fact_repuesto_usado": fact_repuesto,
    }


# ====================================================================== LOAD
ORDEN_CARGA = ["dim_fecha", "dim_cliente", "dim_equipo", "dim_tecnico", "dim_repuesto",
               "fact_orden", "fact_pago", "fact_repuesto_usado"]


def cargar(tablas, inicio):
    motor = create_engine(config.DW)
    ddl = (Path(__file__).parent / "modelo_estrella.sql").read_text(encoding="utf-8")
    with motor.begin() as c:                        # UNA transacción para todo
        c.exec_driver_sql(ddl)
        c.exec_driver_sql("TRUNCATE " + ", ".join(reversed(ORDEN_CARGA)))
        for nombre in ORDEN_CARGA:
            filas = tablas[nombre]
            if filas:
                cols = list(filas[0])
                c.execute(text(f"INSERT INTO {nombre} ({', '.join(cols)}) "
                               f"VALUES ({', '.join(':' + k for k in cols)})"), filas)
            print(f"  cargado   {nombre:20} {len(filas):5} filas")
        fin = datetime.now(COL)
        c.execute(text("INSERT INTO etl_ejecucion (inicio, fin, segundos, filas) VALUES (:i, :f, :s, :filas)"),
                  {"i": inicio, "f": fin, "s": round((fin - inicio).total_seconds(), 2),
                   "filas": json.dumps({k: len(v) for k, v in tablas.items()})})
    motor.dispose()


def main():
    inicio = datetime.now(COL)
    t = time.perf_counter()
    print("1/3 EXTRACT: leyendo las 7 bases de los microservicios")
    datos = extraer()
    print("2/3 TRANSFORM: armando dimensiones y hechos")
    tablas = transformar(datos)
    print("3/3 LOAD: cargando el Data Warehouse (db_dw)")
    cargar(tablas, inicio)
    print(f"ETL terminado en {time.perf_counter() - t:.1f} s")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.exit(f"ERROR en el ETL: {e}")
