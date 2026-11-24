-- =====================================================================
-- DDL de db_ordenes — ms-ordenes (MS3) · puerto 5434
-- Generado con: alembic upgrade head --sql   (misma definición que la migración 0001)
-- Ejecutar conectado a la base db_ordenes (en DBeaver: abrir el script y Alt+X).
-- Normalmente NO hace falta: el microservicio crea las tablas con 'alembic upgrade head'.
-- =====================================================================

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE orden_trabajo (
    id_orden SERIAL NOT NULL, 
    id_equipo INTEGER NOT NULL, 
    id_cliente INTEGER NOT NULL, 
    fecha_recepcion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    descripcion_problema TEXT NOT NULL, 
    accesorios_recibidos VARCHAR(250), 
    prioridad VARCHAR(10) NOT NULL, 
    estado_actual VARCHAR(25) NOT NULL, 
    fecha_cierre TIMESTAMP WITH TIME ZONE, 
    id_usuario_recepcion INTEGER NOT NULL, 
    PRIMARY KEY (id_orden), 
    CONSTRAINT ck_orden_estado CHECK (estado_actual IN ('RECIBIDO','EN_DIAGNOSTICO','ESPERANDO_APROBACION','EN_REPARACION','LISTO_ENTREGA','ENTREGADO','CANCELADO')), 
    CONSTRAINT ck_orden_prioridad CHECK (prioridad IN ('BAJA','MEDIA','ALTA','URGENTE'))
);

CREATE INDEX ix_orden_trabajo_estado_actual ON orden_trabajo (estado_actual);

CREATE INDEX ix_orden_trabajo_id_cliente ON orden_trabajo (id_cliente);

CREATE INDEX ix_orden_trabajo_id_equipo ON orden_trabajo (id_equipo);

CREATE TABLE asignacion (
    id_asignacion SERIAL NOT NULL, 
    id_orden INTEGER NOT NULL, 
    id_tecnico INTEGER NOT NULL, 
    id_usuario_tecnico INTEGER NOT NULL, 
    nombre_tecnico VARCHAR(170) NOT NULL, 
    fecha_asignacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    fecha_finalizacion TIMESTAMP WITH TIME ZONE, 
    estado_asignacion VARCHAR(12) NOT NULL, 
    PRIMARY KEY (id_asignacion), 
    CONSTRAINT ck_asignacion_estado CHECK (estado_asignacion IN ('ACTIVA','FINALIZADA','REASIGNADA')), 
    FOREIGN KEY(id_orden) REFERENCES orden_trabajo (id_orden) ON DELETE RESTRICT
);

CREATE INDEX ix_asignacion_id_orden ON asignacion (id_orden);

CREATE INDEX ix_asignacion_id_tecnico ON asignacion (id_tecnico);

CREATE UNIQUE INDEX uq_asignacion_activa ON asignacion (id_orden) WHERE estado_asignacion = 'ACTIVA';

CREATE TABLE historial_estado (
    id_historial SERIAL NOT NULL, 
    id_orden INTEGER NOT NULL, 
    estado_anterior VARCHAR(25), 
    estado_nuevo VARCHAR(25) NOT NULL, 
    fecha_cambio TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    observacion VARCHAR(500), 
    id_usuario INTEGER NOT NULL, 
    PRIMARY KEY (id_historial), 
    FOREIGN KEY(id_orden) REFERENCES orden_trabajo (id_orden) ON DELETE RESTRICT
);

CREATE INDEX ix_historial_estado_id_orden ON historial_estado (id_orden);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

