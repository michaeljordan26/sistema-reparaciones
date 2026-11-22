-- =====================================================================
-- Data Warehouse del taller (base db_dw) - MODELO EN ESTRELLA
-- 5 dimensiones + 3 tablas de hechos. Lo crea etl.py la primera vez.
-- Granularidad:
--   fact_orden          una fila por orden de trabajo
--   fact_pago           una fila por pago o abono
--   fact_repuesto_usado una fila por repuesto usado en una reparación
-- =====================================================================

-- ---------------------------------------------------------- DIMENSIONES
CREATE TABLE IF NOT EXISTS dim_fecha (
    id_fecha       INTEGER PRIMARY KEY,          -- AAAAMMDD, p. ej. 20261122
    fecha          DATE NOT NULL UNIQUE,
    anio           SMALLINT NOT NULL,
    trimestre      SMALLINT NOT NULL,
    mes            SMALLINT NOT NULL,
    nombre_mes     VARCHAR(12) NOT NULL,
    anio_mes       CHAR(7) NOT NULL,             -- '2026-11', útil para ordenar en los gráficos
    dia            SMALLINT NOT NULL,
    dia_semana     SMALLINT NOT NULL,            -- 1 = lunes ... 7 = domingo
    nombre_dia     VARCHAR(10) NOT NULL,
    es_fin_semana  BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_cliente (
    id_cliente      INTEGER PRIMARY KEY,         -- mismo id de ms-clientes
    documento       VARCHAR(30) NOT NULL,
    nombre          VARCHAR(160) NOT NULL,
    tiene_correo    BOOLEAN NOT NULL,
    fecha_registro  DATE NOT NULL,
    estado          VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_equipo (
    id_equipo    INTEGER PRIMARY KEY,
    tipo_equipo  VARCHAR(20) NOT NULL,
    marca        VARCHAR(60) NOT NULL,
    modelo       VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_tecnico (
    id_tecnico      INTEGER PRIMARY KEY,         -- -1 = "Sin asignar"
    nombre          VARCHAR(160) NOT NULL,
    especialidad    VARCHAR(120),
    estado_laboral  VARCHAR(12) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_repuesto (
    id_repuesto   INTEGER PRIMARY KEY,
    codigo        VARCHAR(30) NOT NULL,
    nombre        VARCHAR(120) NOT NULL,
    categoria     VARCHAR(50) NOT NULL,
    marca         VARCHAR(60),
    precio_costo  NUMERIC(12,2) NOT NULL,
    precio_venta  NUMERIC(12,2) NOT NULL,
    stock_actual  INTEGER NOT NULL,
    stock_minimo  INTEGER NOT NULL,
    stock_bajo    BOOLEAN NOT NULL
);

-- ---------------------------------------------------------- HECHOS
CREATE TABLE IF NOT EXISTS fact_orden (
    id_orden              INTEGER PRIMARY KEY,
    id_fecha_recepcion    INTEGER NOT NULL REFERENCES dim_fecha,
    id_fecha_cierre       INTEGER REFERENCES dim_fecha,
    id_cliente            INTEGER NOT NULL REFERENCES dim_cliente,
    id_equipo             INTEGER NOT NULL REFERENCES dim_equipo,
    id_tecnico            INTEGER NOT NULL REFERENCES dim_tecnico,
    estado                VARCHAR(25) NOT NULL,
    prioridad             VARCHAR(10) NOT NULL,
    decision_presupuesto  VARCHAR(12),            -- APROBADO, RECHAZADO o NULL
    resultado_reparacion  VARCHAR(15),
    abierta               BOOLEAN NOT NULL,
    dias_hasta_cierre     NUMERIC(8,2),           -- de recepción a entrega o cancelación
    horas_hasta_diagnostico NUMERIC(8,2),
    valor_presupuesto     NUMERIC(12,2) NOT NULL DEFAULT 0,
    valor_facturado       NUMERIC(12,2) NOT NULL DEFAULT 0,
    valor_pagado          NUMERIC(12,2) NOT NULL DEFAULT 0,
    saldo_pendiente       NUMERIC(12,2) NOT NULL DEFAULT 0,
    repuestos_usados      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fact_pago (
    id_pago     INTEGER PRIMARY KEY,
    id_fecha    INTEGER NOT NULL REFERENCES dim_fecha,
    id_orden    INTEGER NOT NULL REFERENCES fact_orden,
    id_cliente  INTEGER NOT NULL REFERENCES dim_cliente,
    metodo      VARCHAR(15) NOT NULL,
    tipo        VARCHAR(12) NOT NULL,
    monto       NUMERIC(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_repuesto_usado (
    id_repuesto_utilizado  INTEGER PRIMARY KEY,
    id_fecha     INTEGER NOT NULL REFERENCES dim_fecha,
    id_orden     INTEGER NOT NULL REFERENCES fact_orden,
    id_repuesto  INTEGER NOT NULL REFERENCES dim_repuesto,
    id_tecnico   INTEGER NOT NULL REFERENCES dim_tecnico,
    cantidad     INTEGER NOT NULL,
    valor_venta  NUMERIC(12,2) NOT NULL,
    valor_costo  NUMERIC(12,2) NOT NULL,
    margen       NUMERIC(12,2) NOT NULL
);

-- ---------------------------------------------------------- CONTROL DEL ETL
CREATE TABLE IF NOT EXISTS etl_ejecucion (
    id_ejecucion  SERIAL PRIMARY KEY,
    inicio        TIMESTAMPTZ NOT NULL,
    fin           TIMESTAMPTZ NOT NULL,
    segundos      NUMERIC(8,2) NOT NULL,
    filas         JSONB NOT NULL
);

-- ---------------------------------------------------------- VISTAS PARA CONSULTAR Y PARA POWER BI
CREATE OR REPLACE VIEW vw_ingresos_mensuales AS
SELECT f.anio_mes, f.nombre_mes, p.metodo, count(*) AS pagos, sum(p.monto) AS ingresos
FROM fact_pago p JOIN dim_fecha f ON f.id_fecha = p.id_fecha
GROUP BY f.anio_mes, f.nombre_mes, p.metodo;

CREATE OR REPLACE VIEW vw_ordenes_mensuales AS
SELECT f.anio_mes, f.nombre_mes,
       count(*)                                      AS ordenes,
       count(*) FILTER (WHERE o.estado = 'ENTREGADO') AS entregadas,
       count(*) FILTER (WHERE o.abierta)              AS abiertas,
       round(avg(o.dias_hasta_cierre) FILTER (WHERE o.estado = 'ENTREGADO'), 1) AS dias_promedio
FROM fact_orden o JOIN dim_fecha f ON f.id_fecha = o.id_fecha_recepcion
GROUP BY f.anio_mes, f.nombre_mes;

CREATE OR REPLACE VIEW vw_desempeno_tecnicos AS
SELECT t.nombre AS tecnico,
       count(*)                                        AS ordenes,
       count(*) FILTER (WHERE o.estado = 'ENTREGADO')   AS entregadas,
       round(avg(o.dias_hasta_cierre) FILTER (WHERE o.estado = 'ENTREGADO'), 1) AS dias_promedio,
       sum(o.valor_facturado)                          AS facturado
FROM fact_orden o JOIN dim_tecnico t ON t.id_tecnico = o.id_tecnico
GROUP BY t.nombre;

CREATE OR REPLACE VIEW vw_repuestos_mas_usados AS
SELECT r.codigo, r.nombre, r.categoria,
       sum(u.cantidad) AS unidades, sum(u.valor_venta) AS ventas, sum(u.margen) AS margen
FROM fact_repuesto_usado u JOIN dim_repuesto r ON r.id_repuesto = u.id_repuesto
GROUP BY r.codigo, r.nombre, r.categoria;

CREATE OR REPLACE VIEW vw_indicadores AS
SELECT
    (SELECT count(*) FROM fact_orden)                                     AS total_ordenes,
    (SELECT count(*) FROM fact_orden WHERE abierta)                       AS ordenes_abiertas,
    (SELECT sum(monto) FROM fact_pago)                                    AS ingresos_totales,
    (SELECT sum(saldo_pendiente) FROM fact_orden)                         AS cartera_pendiente,
    (SELECT round(avg(dias_hasta_cierre), 1) FROM fact_orden WHERE estado = 'ENTREGADO') AS dias_promedio_entrega,
    (SELECT round(100.0 * count(*) FILTER (WHERE decision_presupuesto = 'APROBADO')
            / NULLIF(count(*) FILTER (WHERE decision_presupuesto IS NOT NULL), 0), 1)
       FROM fact_orden)                                                   AS tasa_aprobacion_pct,
    (SELECT count(*) FROM dim_repuesto WHERE stock_bajo)                  AS repuestos_stock_bajo;
