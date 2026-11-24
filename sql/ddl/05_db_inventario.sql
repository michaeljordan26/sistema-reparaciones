-- =====================================================================
-- DDL de db_inventario — ms-inventario (MS5) · puerto 5436
-- Generado con: alembic upgrade head --sql   (misma definición que la migración 0001)
-- Ejecutar conectado a la base db_inventario (en DBeaver: abrir el script y Alt+X).
-- Normalmente NO hace falta: el microservicio crea las tablas con 'alembic upgrade head'.
-- =====================================================================

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE repuesto (
    id_repuesto SERIAL NOT NULL, 
    codigo VARCHAR(30) NOT NULL, 
    nombre VARCHAR(120) NOT NULL, 
    descripcion VARCHAR(300), 
    categoria VARCHAR(50) NOT NULL, 
    marca VARCHAR(50), 
    unidad_medida VARCHAR(20) NOT NULL, 
    precio_costo NUMERIC(12, 2) NOT NULL, 
    precio_venta NUMERIC(12, 2) NOT NULL, 
    stock_actual INTEGER NOT NULL, 
    stock_minimo INTEGER NOT NULL, 
    activo BOOLEAN NOT NULL, 
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id_repuesto), 
    CONSTRAINT ck_repuesto_precios CHECK (precio_costo >= 0 AND precio_venta >= 0), 
    CONSTRAINT ck_repuesto_stock_no_negativo CHECK (stock_actual >= 0), 
    CONSTRAINT ck_repuesto_stock_minimo CHECK (stock_minimo >= 0)
);

CREATE INDEX ix_repuesto_categoria ON repuesto (categoria);

CREATE UNIQUE INDEX ix_repuesto_codigo ON repuesto (codigo);

CREATE TABLE movimiento_inventario (
    id_movimiento SERIAL NOT NULL, 
    id_repuesto INTEGER NOT NULL, 
    tipo VARCHAR(20) NOT NULL, 
    cantidad INTEGER NOT NULL, 
    stock_anterior INTEGER NOT NULL, 
    stock_resultante INTEGER NOT NULL, 
    precio_unitario NUMERIC(12, 2), 
    id_orden INTEGER, 
    motivo VARCHAR(300), 
    id_usuario INTEGER NOT NULL, 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id_movimiento), 
    CONSTRAINT ck_movimiento_tipo CHECK (tipo IN ('ENTRADA','SALIDA','DEVOLUCION','AJUSTE_POSITIVO','AJUSTE_NEGATIVO')), 
    CONSTRAINT ck_movimiento_cantidad CHECK (cantidad > 0), 
    CONSTRAINT ck_movimiento_stock_resultante CHECK (stock_resultante >= 0), 
    FOREIGN KEY(id_repuesto) REFERENCES repuesto (id_repuesto) ON DELETE RESTRICT
);

CREATE INDEX ix_movimiento_inventario_id_orden ON movimiento_inventario (id_orden);

CREATE INDEX ix_movimiento_inventario_id_repuesto ON movimiento_inventario (id_repuesto);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

