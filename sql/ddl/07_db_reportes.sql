-- =====================================================================
-- DDL de db_reportes — ms-reportes (MS7) · puerto 5438
-- Generado con: alembic upgrade head --sql   (misma definición que la migración 0001)
-- Ejecutar conectado a la base db_reportes (en DBeaver: abrir el script y Alt+X).
-- Normalmente NO hace falta: el microservicio crea las tablas con 'alembic upgrade head'.
-- =====================================================================

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE notificacion (
    id_notificacion SERIAL NOT NULL, 
    id_orden INTEGER NOT NULL, 
    id_cliente INTEGER, 
    tipo VARCHAR(25) NOT NULL, 
    canal VARCHAR(10) NOT NULL, 
    destinatario VARCHAR(120), 
    asunto VARCHAR(150) NOT NULL, 
    mensaje TEXT NOT NULL, 
    estado VARCHAR(10) NOT NULL, 
    detalle_error VARCHAR(300), 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id_notificacion), 
    CONSTRAINT ck_notificacion_canal CHECK (canal IN ('CORREO','SMS')), 
    CONSTRAINT ck_notificacion_estado CHECK (estado IN ('ENVIADA','FALLIDA')), 
    CONSTRAINT uq_notificacion_orden_tipo UNIQUE (id_orden, tipo)
);

CREATE INDEX ix_notificacion_id_cliente ON notificacion (id_cliente);

CREATE INDEX ix_notificacion_id_orden ON notificacion (id_orden);

CREATE TABLE registro_auditoria (
    id_registro SERIAL NOT NULL, 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    servicio VARCHAR(30) NOT NULL, 
    metodo VARCHAR(6) NOT NULL, 
    ruta VARCHAR(200) NOT NULL, 
    ruta_plantilla VARCHAR(200) NOT NULL, 
    accion VARCHAR(120) NOT NULL, 
    recurso_id VARCHAR(40), 
    codigo_estado INTEGER NOT NULL, 
    exito BOOLEAN NOT NULL, 
    id_usuario INTEGER, 
    roles VARCHAR(120), 
    ip VARCHAR(45), 
    duracion_ms INTEGER, 
    PRIMARY KEY (id_registro), 
    CONSTRAINT ck_auditoria_metodo CHECK (metodo IN ('POST','PUT','PATCH','DELETE'))
);

CREATE INDEX ix_auditoria_servicio_fecha ON registro_auditoria (servicio, fecha);

CREATE INDEX ix_registro_auditoria_fecha ON registro_auditoria (fecha);

CREATE INDEX ix_registro_auditoria_id_usuario ON registro_auditoria (id_usuario);

CREATE OR REPLACE FUNCTION fn_auditoria_inmutable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'La auditoría no se puede modificar ni borrar (operación % bloqueada)', TG_OP;
        END;
        $$ LANGUAGE plpgsql;;

CREATE TRIGGER tg_auditoria_inmutable
        BEFORE UPDATE OR DELETE ON registro_auditoria
        FOR EACH ROW EXECUTE FUNCTION fn_auditoria_inmutable();;

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

