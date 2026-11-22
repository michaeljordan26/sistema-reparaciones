# Sprints 7 y 8 – Data Warehouse, ETL y tablero en Power BI

```
 7 bases OLTP (microservicios)            ETL (Python)                 Data Warehouse (db_dw, puerto 5439)
 db_usuarios     db_clientes      ─┐   EXTRACT  lee cada base     ┌─>  dim_fecha   dim_cliente   dim_equipo
 db_ordenes      db_reparaciones   ├─> TRANSFORM une por id_orden ┤    dim_tecnico dim_repuesto
 db_inventario   db_facturacion   ─┘   LOAD     1 transacción     └─>  fact_orden  fact_pago  fact_repuesto_usado
                                                                         + vistas vw_*  ──>  Power BI
```

| Archivo | Para qué |
|---|---|
| `modelo_estrella.sql` | DDL del Data Warehouse: 5 dimensiones, 3 hechos, control del ETL y 5 vistas |
| `etl.py` | Extrae de las 7 bases, transforma y carga el Data Warehouse (carga completa, repetible) |
| `generar_historico.py` | Crea 6 meses de historia **simulada** por la API real (solo una vez) |
| `config.py` | Lee usuario y contraseña del `.env` de la raíz (nada queda escrito en el código) |

## Ejecutar (con Docker Compose encendido)

1. `docker-iniciar.bat` (ahora son 16 contenedores: se agregó `db-dw`).
2. **Una sola vez:** `dw-historico.bat` → unas 115 órdenes de junio a noviembre (2 a 4 minutos).
3. `dw-etl.bat` → carga el Data Warehouse. Se puede repetir cuando haya datos nuevos.

Comprobación en DBeaver (puerto **5439**, base **db_dw**):

```sql
SELECT * FROM vw_indicadores;
SELECT * FROM vw_ordenes_mensuales ORDER BY anio_mes;
SELECT * FROM etl_ejecucion ORDER BY id_ejecucion DESC;
```

## Tablero en Power BI Desktop (gratis)

**1. Instalar:** Microsoft Store → *Power BI Desktop*.

**2. Conectar:** *Obtener datos* → *Base de datos PostgreSQL*
- Servidor: `localhost:5439` · Base de datos: `db_dw` · Modo: **Importar**
- Credenciales: pestaña *Base de datos*, usuario `taller` y la contraseña de `DB_PASSWORD` de tu `.env`.
- Si pregunta por cifrado: *Aceptar* (conexión local sin cifrar).
- Marca las 8 tablas `dim_*` y `fact_*` → *Cargar*.

**3. Relaciones** (vista *Modelo*, el ícono de las tres cajas). Deja solo estas; borra cualquier otra que Power BI
haya creado entre dos tablas `fact_*`:

| Desde (muchos) | Hacia (uno) |
|---|---|
| `fact_orden[id_fecha_recepcion]` | `dim_fecha[id_fecha]` |
| `fact_orden[id_cliente]` / `[id_equipo]` / `[id_tecnico]` | `dim_cliente` / `dim_equipo` / `dim_tecnico` |
| `fact_pago[id_fecha]` | `dim_fecha[id_fecha]` |
| `fact_pago[id_cliente]` | `dim_cliente[id_cliente]` |
| `fact_repuesto_usado[id_fecha]` | `dim_fecha[id_fecha]` |
| `fact_repuesto_usado[id_repuesto]` / `[id_tecnico]` | `dim_repuesto` / `dim_tecnico` |

**4. Medidas** (*Modelado* → *Nueva medida*, una por una):

```DAX
Órdenes = COUNTROWS(fact_orden)
Ingresos = SUM(fact_pago[monto])
Cartera pendiente = SUM(fact_orden[saldo_pendiente])
Días promedio entrega = CALCULATE(AVERAGE(fact_orden[dias_hasta_cierre]), fact_orden[estado] = "ENTREGADO")
Tasa aprobación = DIVIDE(
    CALCULATE(COUNTROWS(fact_orden), fact_orden[decision_presupuesto] = "APROBADO"),
    CALCULATE(COUNTROWS(fact_orden), NOT ISBLANK(fact_orden[decision_presupuesto])))
Margen repuestos = SUM(fact_repuesto_usado[margen])
```

Selecciona `Tasa aprobación` y en *Herramientas de medidas* ponle formato de porcentaje.

**5. Visualizaciones** (una página, *Tablero del taller*):

| Visual | Campos |
|---|---|
| 4 tarjetas | `Órdenes`, `Ingresos`, `Días promedio entrega`, `Tasa aprobación` |
| Gráfico de líneas | Eje X: `dim_fecha[anio_mes]` · Y: `Ingresos` |
| Columnas agrupadas | Eje X: `dim_fecha[anio_mes]` · Y: `Órdenes` |
| Anillo | Leyenda: `fact_pago[metodo]` · Valores: `Ingresos` |
| Barras | Eje Y: `dim_tecnico[nombre]` · X: `Órdenes` |
| Barras | Eje Y: `dim_repuesto[codigo]` · X: suma de `fact_repuesto_usado[cantidad]` |
| Segmentación | `dim_fecha[nombre_mes]` (filtra toda la página) |

Guarda el archivo como `docs/tablero-taller.pbix`.

**6. Actualizar:** cuando haya datos nuevos, ejecuta `dw-etl.bat` y en Power BI pulsa **Actualizar**.

> Los datos de `generar_historico.py` son **simulados** para demostrar el análisis; todo lo demás
> (reglas, cálculos y flujo) es el sistema real.
