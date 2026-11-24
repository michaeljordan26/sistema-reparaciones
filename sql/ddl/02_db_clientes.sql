-- =====================================================================
-- DDL de db_clientes — ms-clientes (MS2) · puerto 5433
-- Generado con: alembic upgrade head --sql   (misma definición que la migración 0001)
-- Ejecutar conectado a la base db_clientes (en DBeaver: abrir el script y Alt+X).
-- Normalmente NO hace falta: el microservicio crea las tablas con 'alembic upgrade head'.
-- =====================================================================

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE cliente (
    id_cliente SERIAL NOT NULL, 
    tipo_documento VARCHAR(5) NOT NULL, 
    numero_documento VARCHAR(20) NOT NULL, 
    nombres VARCHAR(80) NOT NULL, 
    apellidos VARCHAR(80) NOT NULL, 
    telefono VARCHAR(20) NOT NULL, 
    correo VARCHAR(120), 
    direccion VARCHAR(150), 
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    estado VARCHAR(10) NOT NULL, 
    PRIMARY KEY (id_cliente), 
    CONSTRAINT ck_cliente_estado CHECK (estado IN ('ACTIVO','INACTIVO')), 
    CONSTRAINT ck_cliente_tipo_doc CHECK (tipo_documento IN ('CC','CE','NIT','TI','PAS')), 
    CONSTRAINT uq_cliente_documento UNIQUE (tipo_documento, numero_documento)
);

CREATE INDEX ix_cliente_numero_documento ON cliente (numero_documento);

CREATE TABLE equipo (
    id_equipo SERIAL NOT NULL, 
    id_cliente INTEGER NOT NULL, 
    tipo_equipo VARCHAR(20) NOT NULL, 
    marca VARCHAR(50) NOT NULL, 
    modelo VARCHAR(80) NOT NULL, 
    numero_serie VARCHAR(80) NOT NULL, 
    descripcion VARCHAR(300), 
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    estado VARCHAR(10) NOT NULL, 
    PRIMARY KEY (id_equipo), 
    CONSTRAINT ck_equipo_estado CHECK (estado IN ('ACTIVO','INACTIVO')), 
    CONSTRAINT ck_equipo_tipo CHECK (tipo_equipo IN ('PORTATIL','ESCRITORIO','TODO_EN_UNO','IMPRESORA','TABLET','SERVIDOR','OTRO')), 
    FOREIGN KEY(id_cliente) REFERENCES cliente (id_cliente) ON DELETE RESTRICT
);

CREATE INDEX ix_equipo_id_cliente ON equipo (id_cliente);

CREATE UNIQUE INDEX ix_equipo_numero_serie ON equipo (numero_serie);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

