"""Genera ~6 meses de historia SIMULADA para el Data Warehouse.

Cómo funciona:
1. Recorre el flujo completo por la API real (recepción, diagnóstico, presupuesto, reparación,
   repuestos, factura, pagos y entrega), así se respetan todas las reglas y las 7 bases quedan
   coherentes entre sí.
2. Después "mueve hacia atrás" las fechas de cada orden en las bases, para que haya datos de
   varios meses (las API siempre guardan la fecha de hoy).

Se ejecuta UNA sola vez, con el sistema encendido (docker compose up -d):
    python generar_historico.py
"""
import random
import sys
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import create_engine, text

import config

COL = ZoneInfo("America/Bogota")
random.seed(2026)
PRIMER_DOCUMENTO = 1090000001          # Documentos de los clientes simulados
http = httpx.Client(timeout=30)


# ---------------------------------------------------------------- utilidades HTTP
def login(usuario):
    r = http.post(f"{config.API['usuarios']}/auth/login",
                  data={"username": usuario, "password": config.CREDENCIALES[usuario]})
    if r.status_code != 200:
        sys.exit(f"No se pudo iniciar sesión como {usuario}: {r.text}")
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def llamar(metodo, servicio, ruta, token, **kw):
    r = http.request(metodo, f"{config.API[servicio]}{ruta}", headers=token, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"{metodo} {servicio}{ruta} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.content else None


# ---------------------------------------------------------------- catálogos de ejemplo
NOMBRES = ["Andrés", "Paula", "Felipe", "Natalia", "Santiago", "Valentina", "Julián", "Daniela", "Camilo",
           "Juliana", "Sebastián", "Laura", "Diego", "Catalina", "Mateo", "Sara", "Nicolás", "Mariana",
           "Óscar", "Lina", "Ricardo", "Gabriela", "Esteban", "Isabel", "Tomás", "Ángela", "David", "Carolina"]
APELLIDOS = ["Rodríguez", "Gómez", "González", "Martínez", "García", "López", "Hernández", "Sánchez",
             "Ramírez", "Torres", "Díaz", "Moreno", "Rojas", "Vargas", "Castro", "Ortiz", "Jiménez", "Suárez"]
EQUIPOS = [
    ("PORTATIL", "Lenovo", "IdeaPad 3"), ("PORTATIL", "HP", "Pavilion 15"), ("PORTATIL", "Asus", "VivoBook 15"),
    ("PORTATIL", "Dell", "Inspiron 15"), ("PORTATIL", "Acer", "Aspire 5"), ("ESCRITORIO", "Dell", "OptiPlex 3080"),
    ("ESCRITORIO", "HP", "ProDesk 400"), ("TODO_EN_UNO", "Lenovo", "IdeaCentre AIO 3"),
    ("IMPRESORA", "Epson", "L3250"), ("IMPRESORA", "HP", "Smart Tank 515"), ("TABLET", "Samsung", "Galaxy Tab A8"),
]
# problema, causa, solución, repuestos sugeridos (códigos), horas de mano de obra
FALLAS = {
    "PORTATIL": [
        ("No enciende y no carga la batería", "Jack de carga dañado", "Cambiar el jack DC", ["JACK-DC-LEN"], 1.5),
        ("Está muy lento y se congela", "Poca memoria RAM y disco mecánico", "Ampliar RAM y cambiar a SSD",
         ["RAM-DDR4-8GB", "SSD-480GB"], 2),
        ("Se calienta y se apaga solo", "Ventilador obstruido y pasta térmica seca", "Limpieza interna y pasta térmica",
         ["PASTA-TERM"], 1),
        ("Varias teclas no responden", "Teclado dañado por derrame de líquido", "Cambiar el teclado", ["TECL-HP-15"], 1),
        ("La pantalla tiene rayas y parpadea", "Panel LCD dañado", "Cambiar la pantalla", ["PANT-156-FHD"], 1.5),
        ("Windows no arranca", "Sistema operativo dañado", "Reinstalar el sistema y respaldar datos", [], 2.5),
    ],
    "ESCRITORIO": [
        ("No enciende", "Fuente de poder quemada", "Cambiar la fuente", ["FUENTE-500W"], 1),
        ("Muy lento al iniciar", "Disco mecánico con sectores dañados", "Cambiar a SSD y migrar datos",
         ["SSD-NVME-1TB"], 2),
        ("Se reinicia solo", "Sobrecalentamiento del procesador", "Limpieza y pasta térmica", ["PASTA-TERM"], 1),
    ],
    "TODO_EN_UNO": [
        ("Muy lento", "Disco duro lento y poca RAM", "Instalar SSD y RAM", ["SSD-480GB", "RAM-DDR4-8GB"], 2.5),
    ],
    "IMPRESORA": [
        ("Atasca el papel", "Rodillo de arrastre gastado", "Limpieza y ajuste del mecanismo", [], 1.5),
        ("Imprime con rayas", "Cabezal obstruido", "Limpieza profunda del cabezal", [], 1),
    ],
    "TABLET": [
        ("No carga", "Puerto de carga sucio", "Limpieza del puerto de carga", [], 0.5),
    ],
}
METODOS = ["EFECTIVO", "EFECTIVO", "NEQUI", "TARJETA", "TRANSFERENCIA", "DAVIPLATA"]
MEDIOS = ["PRESENCIAL", "TELEFONO", "WHATSAPP", "CORREO"]
PRIORIDADES = ["BAJA", "MEDIA", "MEDIA", "MEDIA", "ALTA", "ALTA", "URGENTE"]


def hora_habil(dia: date) -> datetime:
    return datetime.combine(dia, time(random.randint(8, 16), random.randint(0, 59)), tzinfo=COL)


def planear_ordenes(hoy: date):
    """Cuántas órdenes por mes y en qué fecha llegan (el negocio crece mes a mes)."""
    primero = date(hoy.year, hoy.month, 1)
    meses = []
    for _ in range(6):
        meses.insert(0, primero)
        primero = (primero - timedelta(days=1)).replace(day=1)
    fechas = []
    for i, inicio in enumerate(meses):
        fin = (inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        fin = min(fin, hoy - timedelta(days=1))
        cantidad = 12 + 3 * i + random.randint(0, 3)
        if inicio.month == hoy.month:
            cantidad = max(4, int(cantidad * (hoy.day - 1) / 30))
        for _ in range(cantidad):
            dia = inicio + timedelta(days=random.randint(0, (fin - inicio).days))
            if dia.weekday() == 6:                      # domingo cerrado
                dia += timedelta(days=1)
            if dia < hoy:
                fechas.append(hora_habil(dia))
    return sorted(fechas)


def main():
    hoy = datetime.now(COL).date()
    bd = {k: create_engine(v) for k, v in config.ORIGENES.items()}

    with bd["clientes"].connect() as c:
        if c.scalar(text("SELECT count(*) FROM cliente WHERE numero_documento = :d"),
                    {"d": str(PRIMER_DOCUMENTO)}):
            sys.exit("La historia simulada ya existe. Para empezar de cero: reiniciar-datos.bat "
                     "o docker compose down -v")

    print("Iniciando sesión con los usuarios de prueba...")
    tk = {u: login(u) for u in config.CREDENCIALES}
    tecnicos = [t for t in llamar("GET", "usuarios", "/tecnicos", tk["admin"]) if t["estado_laboral"] == "ACTIVO"]
    usuario_de = {}
    for nombre in ("tecnico1", "tecnico2"):
        yo = llamar("GET", "usuarios", "/auth/me", tk[nombre])
        usuario_de[yo["id_usuario"]] = nombre
    tecnicos = [t for t in tecnicos if t["id_usuario"] in usuario_de]
    repuestos = {r["codigo"]: r for r in llamar("GET", "inventario", "/repuestos", tk["inventario"])}

    plan = planear_ordenes(hoy)
    print(f"Se simularán {len(plan)} órdenes entre {plan[0]:%d/%m/%Y} y {plan[-1]:%d/%m/%Y}.")

    clientes = []          # [(id_cliente, [id_equipo...], fecha_registro)]
    ajustes = []           # fechas a corregir al final
    mes_abastecido = None
    sig_doc = PRIMER_DOCUMENTO

    for n, t0 in enumerate(plan, start=1):
        # --- compra mensual de repuestos (entradas al inventario) ---
        if mes_abastecido != (t0.year, t0.month):
            mes_abastecido = (t0.year, t0.month)
            for cod, rep in repuestos.items():
                mov = llamar("POST", "inventario", f"/repuestos/{rep['id_repuesto']}/entradas", tk["inventario"],
                             json={"cantidad": random.randint(1, 4), "motivo": "Compra mensual a proveedor"})
                ajustes.append(("inventario", "UPDATE movimiento_inventario SET fecha = :f WHERE id_movimiento = :id",
                                {"f": t0.replace(hour=7, minute=30) - timedelta(days=1), "id": mov["id_movimiento"]}))

        # --- cliente nuevo o recurrente ---
        if not clientes or random.random() < 0.7:
            nombre, apellido = random.choice(NOMBRES), f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
            cli = llamar("POST", "clientes", "/clientes", tk["recepcion"], json={
                "tipo_documento": "CC", "numero_documento": str(sig_doc), "nombres": nombre, "apellidos": apellido,
                "telefono": f"3{random.randint(100000000, 299999999)}",
                "correo": f"cliente{sig_doc}@correo.com"})
            sig_doc += 1
            tipo, marca, modelo = random.choice(EQUIPOS)
            eq = llamar("POST", "clientes", "/equipos", tk["recepcion"], json={
                "id_cliente": cli["id_cliente"], "tipo_equipo": tipo, "marca": marca, "modelo": modelo,
                "numero_serie": f"SN{sig_doc}{random.randint(100, 999)}"})
            clientes.append((cli["id_cliente"], [(eq["id_equipo"], tipo)]))
            alta = t0 - timedelta(minutes=10)
            ajustes += [("clientes", "UPDATE cliente SET fecha_registro = :f WHERE id_cliente = :id",
                         {"f": alta, "id": cli["id_cliente"]}),
                        ("clientes", "UPDATE equipo SET fecha_registro = :f WHERE id_equipo = :id",
                         {"f": alta, "id": eq["id_equipo"]})]
        id_cliente, equipos = random.choice(clientes)
        id_equipo, tipo = random.choice(equipos)
        problema, causa, solucion, cods, horas = random.choice(FALLAS[tipo])

        # --- línea de tiempo de la orden ---
        dias_atras = (hoy - t0.date()).days
        if dias_atras <= 2:
            destino = random.choice(["RECIBIDO", "EN_DIAGNOSTICO"])
        elif dias_atras <= 7:
            destino = random.choice(["ESPERANDO_APROBACION", "EN_REPARACION", "LISTO_ENTREGA", "ENTREGADO"])
        else:
            destino = random.choices(["ENTREGADO", "RECHAZADO", "CANCELADO"], [85, 10, 5])[0]
        t = {"RECIBIDO": t0}
        t["EN_DIAGNOSTICO"] = t["RECIBIDO"] + timedelta(hours=random.uniform(2, 26))
        t["ESPERANDO_APROBACION"] = t["EN_DIAGNOSTICO"] + timedelta(hours=random.uniform(2, 20))
        t["EN_REPARACION"] = t["ESPERANDO_APROBACION"] + timedelta(hours=random.uniform(3, 48))
        t["LISTO_ENTREGA"] = t["EN_REPARACION"] + timedelta(hours=random.uniform(4, 96))
        t["ENTREGADO"] = t["LISTO_ENTREGA"] + timedelta(hours=random.uniform(2, 72))
        t["CANCELADO"] = t["RECIBIDO"] + timedelta(hours=random.uniform(1, 30))
        # Ninguna etapa puede quedar en el futuro (órdenes de los últimos días)
        ahora = datetime.now(COL) - timedelta(hours=1)
        for i, etapa in enumerate(["RECIBIDO", "EN_DIAGNOSTICO", "ESPERANDO_APROBACION", "EN_REPARACION",
                                   "LISTO_ENTREGA", "ENTREGADO"]):
            t[etapa] = min(t[etapa], ahora - timedelta(minutes=10 * (5 - i)))
        t["CANCELADO"] = min(t["CANCELADO"], ahora)

        # --- 1. recepción y asignación ---
        orden = llamar("POST", "ordenes", "/ordenes", tk["recepcion"], json={
            "id_equipo": id_equipo, "descripcion_problema": problema, "accesorios_recibidos": "Cargador",
            "prioridad": random.choice(PRIORIDADES)})
        oid = orden["id_orden"]
        tec = random.choice(tecnicos)
        tk_tec = tk[usuario_de[tec["id_usuario"]]]
        llamar("POST", "ordenes", f"/ordenes/{oid}/asignar", tk["recepcion"], json={"id_tecnico": tec["id_tecnico"]})
        estados = ["RECIBIDO"]

        if destino == "CANCELADO":
            llamar("PATCH", "ordenes", f"/ordenes/{oid}/estado", tk["recepcion"],
                   json={"estado": "CANCELADO", "observacion": "El cliente retiró el equipo sin revisión"})
            estados.append("CANCELADO")
        elif destino != "RECIBIDO":
            # --- 2. diagnóstico ---
            llamar("PATCH", "ordenes", f"/ordenes/{oid}/estado", tk_tec, json={"estado": "EN_DIAGNOSTICO"})
            estados.append("EN_DIAGNOSTICO")
            if destino != "EN_DIAGNOSTICO":
                llamar("POST", "reparaciones", "/diagnosticos", tk_tec, json={
                    "id_orden": oid, "hallazgos": f"{problema}. Revisión completa del equipo.",
                    "causa_probable": causa, "solucion_propuesta": solucion, "requiere_repuestos": bool(cods)})
                estados.append("ESPERANDO_APROBACION")
                # --- 3. presupuesto ---
                usar = [c for c in cods if c in repuestos]
                pres = llamar("POST", "facturacion", "/presupuestos", tk_tec, json={
                    "id_orden": oid,
                    "mano_obra": [{"descripcion": solucion, "horas": horas, "valor_hora": 45000}],
                    "repuestos": [{"id_repuesto": repuestos[c]["id_repuesto"], "cantidad": 1} for c in usar]})
                if destino != "ESPERANDO_APROBACION":
                    decision = "RECHAZADO" if destino == "RECHAZADO" else "APROBADO"
                    llamar("POST", "facturacion", f"/presupuestos/{pres['id_presupuesto']}/respuesta",
                           tk["recepcion"], json={"decision": decision, "medio": random.choice(MEDIOS),
                                                  "nombre_responde": "Titular de la orden"})
                    if decision == "RECHAZADO":
                        estados.append("LISTO_ENTREGA")
                        t["LISTO_ENTREGA"] = t["EN_REPARACION"]
                        llamar("PATCH", "ordenes", f"/ordenes/{oid}/estado", tk["recepcion"],
                               json={"estado": "ENTREGADO", "observacion": "Se devuelve sin reparar"})
                        estados.append("ENTREGADO")
                        t["ENTREGADO"] = t["LISTO_ENTREGA"] + timedelta(hours=random.uniform(2, 48))
                    else:
                        estados.append("EN_REPARACION")
                        # --- 4. reparación y repuestos ---
                        rep = llamar("POST", "reparaciones", "/reparaciones", tk_tec, json={"id_orden": oid})
                        for c in usar:
                            try:
                                llamar("POST", "reparaciones", f"/reparaciones/{rep['id_reparacion']}/repuestos",
                                       tk_tec, json={"id_repuesto": repuestos[c]["id_repuesto"], "cantidad": 1})
                            except RuntimeError as e:      # sin existencias: se repara sin ese repuesto
                                print(f"    (orden {oid}: {c} sin existencias, se omite)")
                        if destino in ("LISTO_ENTREGA", "ENTREGADO"):
                            llamar("POST", "reparaciones", f"/reparaciones/{rep['id_reparacion']}/finalizar", tk_tec,
                                   json={"actividades_realizadas": f"{solucion}. Pruebas de funcionamiento correctas.",
                                         "resultado": "EXITOSA"})
                            estados.append("LISTO_ENTREGA")
                        if destino == "LISTO_ENTREGA":
                            # Listo pero sin recoger: factura con un abono del 50 % (queda saldo en cartera)
                            fac = llamar("POST", "facturacion", "/facturas", tk["caja"], json={"id_orden": oid})
                            pago = llamar("POST", "facturacion", f"/facturas/{fac['id_factura']}/pagos", tk["caja"],
                                          json={"monto": round(float(fac["total"]) * 0.5, -3), "metodo": "EFECTIVO"})
                            ajustes += [("facturacion", "UPDATE factura SET fecha = :f WHERE id_orden = :o",
                                         {"f": t["LISTO_ENTREGA"] + timedelta(minutes=30), "o": oid}),
                                        ("facturacion", "UPDATE pago SET fecha = :f WHERE id_pago = :id",
                                         {"f": t["LISTO_ENTREGA"] + timedelta(minutes=35), "id": pago["id_pago"]})]
                        if destino == "ENTREGADO":
                            # --- 5. factura, pagos y entrega ---
                            fac = llamar("POST", "facturacion", "/facturas", tk["caja"], json={"id_orden": oid})
                            saldo = float(fac["total"])
                            pagos = [saldo] if random.random() < 0.7 else [round(saldo * 0.5, -3), None]
                            for i, monto in enumerate(pagos):
                                monto = monto if monto is not None else round(saldo - pagos[0], 2)
                                metodo = random.choice(METODOS)
                                pago = llamar("POST", "facturacion", f"/facturas/{fac['id_factura']}/pagos",
                                              tk["caja"], json={
                                                  "monto": monto, "metodo": metodo,
                                                  "referencia": None if metodo == "EFECTIVO"
                                                  else f"REF{random.randint(100000, 999999)}"})
                                cuando = t["ENTREGADO"] - timedelta(minutes=20 - 10 * i)
                                ajustes.append(("facturacion", "UPDATE pago SET fecha = :f WHERE id_pago = :id",
                                                {"f": cuando, "id": pago["id_pago"]}))
                            ajustes.append(("facturacion", "UPDATE factura SET fecha = :f WHERE id_orden = :o",
                                            {"f": t["ENTREGADO"] - timedelta(minutes=30), "o": oid}))
                            llamar("PATCH", "ordenes", f"/ordenes/{oid}/estado", tk["recepcion"],
                                   json={"estado": "ENTREGADO", "observacion": "Entregado al cliente"})
                            estados.append("ENTREGADO")

        ajustes.append(("orden", oid, {e: t[e] for e in estados}))
        if n % 10 == 0 or n == len(plan):
            print(f"  {n}/{len(plan)} órdenes")

    print("Ajustando las fechas en las 7 bases...")
    aplicar_fechas(bd, ajustes)
    print("Listo. Ahora ejecuta:  python etl.py")


def aplicar_fechas(bd, ajustes):
    """Todas las correcciones en una transacción por base: o se aplican todas o ninguna."""
    conns = {k: e.connect() for k, e in bd.items()}
    trans = {k: c.begin() for k, c in conns.items()}
    try:
        for item in ajustes:
            if item[0] != "orden":
                servicio, sql, params = item
                conns[servicio].execute(text(sql), params)
                continue
            _, oid, t = item
            fin = t.get("ENTREGADO") or t.get("CANCELADO")
            o, r, f, i, n = (conns[k] for k in ("ordenes", "reparaciones", "facturacion", "inventario", "reportes"))
            o.execute(text("UPDATE orden_trabajo SET fecha_recepcion = :t0, "
                           "fecha_cierre = CASE WHEN fecha_cierre IS NULL THEN NULL ELSE CAST(:fin AS timestamptz) END WHERE id_orden = :o"),
                      {"t0": t["RECIBIDO"], "fin": fin, "o": oid})
            o.execute(text("UPDATE asignacion SET fecha_asignacion = :a, fecha_finalizacion = CASE WHEN "
                           "fecha_finalizacion IS NULL THEN NULL ELSE CAST(:fin AS timestamptz) END WHERE id_orden = :o"),
                      {"a": t["RECIBIDO"] + timedelta(minutes=15), "fin": fin, "o": oid})
            for estado, cuando in t.items():
                o.execute(text("UPDATE historial_estado SET fecha_cambio = :f WHERE id_orden = :o AND estado_nuevo = :e"),
                          {"f": cuando, "o": oid, "e": estado})
                n.execute(text("UPDATE notificacion SET fecha = :f WHERE id_orden = :o AND tipo = :e"),
                          {"f": cuando + timedelta(minutes=1), "o": oid, "e": estado})
            if "ESPERANDO_APROBACION" in t:
                d = t["ESPERANDO_APROBACION"]
                r.execute(text("UPDATE diagnostico SET fecha = :f WHERE id_orden = :o"), {"f": d, "o": oid})
                f.execute(text("UPDATE presupuesto SET fecha = :d, fecha_vencimiento = :v, fecha_creacion = :f "
                               "WHERE id_orden = :o"),
                          {"d": d.date(), "v": d.date() + timedelta(days=15), "f": d, "o": oid})
            if "EN_REPARACION" in t or "LISTO_ENTREGA" in t:
                resp = t.get("EN_REPARACION") or t["LISTO_ENTREGA"]
                f.execute(text("UPDATE respuesta_presupuesto SET fecha = :f WHERE id_presupuesto IN "
                               "(SELECT id_presupuesto FROM presupuesto WHERE id_orden = :o)"), {"f": resp, "o": oid})
            if "EN_REPARACION" in t:
                ini, uso = t["EN_REPARACION"], t["EN_REPARACION"] + timedelta(hours=2)
                r.execute(text("UPDATE reparacion SET fecha_inicio = :i, fecha_fin = CASE WHEN fecha_fin IS NULL "
                               "THEN NULL ELSE CAST(:l AS timestamptz) END WHERE id_orden = :o"),
                          {"i": ini, "l": t.get("LISTO_ENTREGA"), "o": oid})
                r.execute(text("UPDATE repuesto_utilizado SET fecha = :u WHERE id_reparacion IN "
                               "(SELECT id_reparacion FROM reparacion WHERE id_orden = :o)"), {"u": uso, "o": oid})
                i.execute(text("UPDATE movimiento_inventario SET fecha = :u WHERE id_orden = :o"), {"u": uso, "o": oid})
                if "LISTO_ENTREGA" in t:
                    inicio = t["LISTO_ENTREGA"].date()
                    r.execute(text("UPDATE garantia SET fecha_inicio = :i, fecha_fin = CAST(:i AS date) + dias WHERE id_orden = :o"),
                              {"i": inicio, "o": oid})
        for t_ in trans.values():
            t_.commit()
    except Exception:
        for t_ in trans.values():
            t_.rollback()
        raise
    finally:
        for c in conns.values():
            c.close()


if __name__ == "__main__":
    main()
