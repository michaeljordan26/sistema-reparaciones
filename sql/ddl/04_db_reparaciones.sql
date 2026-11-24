-- =====================================================================
-- DDL de db_reparaciones — ms-reparaciones (MS4) · puerto 5435
-- Generado con: alembic upgrade head --sql   (misma definición que la migración 0001)
-- Ejecutar conectado a la base db_reparaciones (en DBeaver: abrir el script y Alt+X).
-- Normalmente NO hace falta: el microservicio crea las tablas con 'alembic upgrade head'.
-- =====================================================================

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE diagnostico (
    id_diagnostico SERIAL NOT NULL, 
    id_orden INTEGER NOT NULL, 
    id_tecnico INTEGER NOT NULL, 
    id_usuario_tecnico INTEGER NOT NULL, 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    hallazgos TEXT NOT NULL, 
    causa_probable VARCHAR(500) NOT NULL, 
    solucion_propuesta TEXT NOT NULL, 
    requiere_repuestos BOOLEAN NOT NULL, 
    tiempo_estimado_horas NUMERIC(5, 1), 
    observaciones VARCHAR(500), 
    PRIMARY KEY (id_diagnostico), 
    CONSTRAINT ck_diagnostico_tiempo CHECK (tiempo_estimado_horas IS NULL OR tiempo_estimado_horas > 0)
);

CREATE UNIQUE INDEX ix_diagnostico_id_orden ON diagnostico (id_orden);

CREATE TABLE reparacion (
    id_reparacion SERIAL NOT NULL, 
    id_orden INTEGER NOT NULL, 
    id_diagnostico INTEGER NOT NULL, 
    id_tecnico INTEGER NOT NULL, 
    id_usuario_tecnico INTEGER NOT NULL, 
    fecha_inicio TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    fecha_fin TIMESTAMP WITH TIME ZONE, 
    actividades_realizadas TEXT, 
    resultado VARCHAR(15), 
    observaciones VARCHAR(500), 
    estado VARCHAR(12) NOT NULL, 
    PRIMARY KEY (id_reparacion), 
    CONSTRAINT ck_reparacion_fin CHECK ((estado = 'FINALIZADA') = (fecha_fin IS NOT NULL)), 
    CONSTRAINT ck_reparacion_estado CHECK (estado IN ('EN_PROCESO','FINALIZADA')), 
    CONSTRAINT ck_reparacion_resultado CHECK (resultado IS NULL OR resultado IN ('EXITOSA','PARCIAL','NO_REPARABLE')), 
    FOREIGN KEY(id_diagnostico) REFERENCES diagnostico (id_diagnostico) ON DELETE RESTRICT, 
    UNIQUE (id_diagnostico)
);

CREATE UNIQUE INDEX ix_reparacion_id_orden ON reparacion (id_orden);

CREATE TABLE garantia (
    id_garantia SERIAL NOT NULL, 
    id_reparacion INTEGER NOT NULL, 
    id_orden INTEGER NOT NULL, 
    id_equipo INTEGER NOT NULL, 
    id_cliente INTEGER NOT NULL, 
    fecha_inicio DATE NOT NULL, 
    fecha_fin DATE NOT NULL, 
    dias INTEGER NOT NULL, 
    cobertura VARCHAR(500) NOT NULL, 
    condiciones VARCHAR(500), 
    anulada BOOLEAN NOT NULL, 
    motivo_anulacion VARCHAR(300), 
    PRIMARY KEY (id_garantia), 
    CONSTRAINT ck_garantia_dias CHECK (dias > 0), 
    CONSTRAINT ck_garantia_fechas CHECK (fecha_fin >= fecha_inicio), 
    FOREIGN KEY(id_reparacion) REFERENCES reparacion (id_reparacion) ON DELETE RESTRICT, 
    UNIQUE (id_reparacion)
);

CREATE INDEX ix_garantia_id_cliente ON garantia (id_cliente);

CREATE INDEX ix_garantia_id_equipo ON garantia (id_equipo);

CREATE INDEX ix_garantia_id_orden ON garantia (id_orden);

CREATE TABLE repuesto_utilizado (
    id_repuesto_utilizado SERIAL NOT NULL, 
    id_reparacion INTEGER NOT NULL, 
    id_repuesto INTEGER NOT NULL, 
    id_movimiento INTEGER NOT NULL, 
    codigo VARCHAR(30) NOT NULL, 
    nombre VARCHAR(120) NOT NULL, 
    cantidad INTEGER NOT NULL, 
    precio_unitario NUMERIC(12, 2) NOT NULL, 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id_repuesto_utilizado), 
    CONSTRAINT ck_ru_cantidad CHECK (cantidad > 0), 
    FOREIGN KEY(id_reparacion) REFERENCES reparacion (id_reparacion) ON DELETE CASCADE
);

CREATE INDEX ix_repuesto_utilizado_id_reparacion ON repuesto_utilizado (id_reparacion);

CREATE TABLE reclamacion_garantia (
    id_reclamacion SERIAL NOT NULL, 
    id_garantia INTEGER NOT NULL, 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    descripcion TEXT NOT NULL, 
    estado VARCHAR(10) NOT NULL, 
    respuesta VARCHAR(500), 
    fecha_respuesta TIMESTAMP WITH TIME ZONE, 
    id_usuario_registro INTEGER NOT NULL, 
    id_usuario_respuesta INTEGER, 
    PRIMARY KEY (id_reclamacion), 
    CONSTRAINT ck_reclamacion_estado CHECK (estado IN ('ABIERTA','APROBADA','RECHAZADA')), 
    FOREIGN KEY(id_garantia) REFERENCES garantia (id_garantia) ON DELETE RESTRICT
);

CREATE INDEX ix_reclamacion_garantia_id_garantia ON reclamacion_garantia (id_garantia);

CREATE UNIQUE INDEX uq_reclamacion_abierta ON reclamacion_garantia (id_garantia) WHERE estado = 'ABIERTA';

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

