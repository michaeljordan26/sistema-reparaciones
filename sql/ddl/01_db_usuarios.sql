-- =====================================================================
-- DDL de db_usuarios — ms-usuarios (MS1) · puerto 5432
-- Generado con: alembic upgrade head --sql   (misma definición que la migración 0001)
-- Ejecutar conectado a la base db_usuarios (en DBeaver: abrir el script y Alt+X).
-- Normalmente NO hace falta: el microservicio crea las tablas con 'alembic upgrade head'.
-- =====================================================================

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE rol (
    id_rol SERIAL NOT NULL, 
    nombre VARCHAR(30) NOT NULL, 
    descripcion VARCHAR(200), 
    PRIMARY KEY (id_rol), 
    UNIQUE (nombre)
);

CREATE TABLE usuario (
    id_usuario SERIAL NOT NULL, 
    nombres VARCHAR(80) NOT NULL, 
    apellidos VARCHAR(80) NOT NULL, 
    correo VARCHAR(120) NOT NULL, 
    nombre_usuario VARCHAR(50) NOT NULL, 
    contrasena_hash VARCHAR(255) NOT NULL, 
    activo BOOLEAN NOT NULL, 
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id_usuario)
);

CREATE UNIQUE INDEX ix_usuario_correo ON usuario (correo);

CREATE UNIQUE INDEX ix_usuario_nombre_usuario ON usuario (nombre_usuario);

CREATE TABLE tecnico (
    id_tecnico SERIAL NOT NULL, 
    id_usuario INTEGER NOT NULL, 
    especialidad VARCHAR(100) NOT NULL, 
    estado_laboral VARCHAR(20) NOT NULL, 
    PRIMARY KEY (id_tecnico), 
    CONSTRAINT ck_tecnico_estado CHECK (estado_laboral IN ('ACTIVO','VACACIONES','INACTIVO')), 
    FOREIGN KEY(id_usuario) REFERENCES usuario (id_usuario) ON DELETE CASCADE, 
    UNIQUE (id_usuario)
);

CREATE TABLE usuario_rol (
    id_usuario INTEGER NOT NULL, 
    id_rol INTEGER NOT NULL, 
    fecha_asignacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id_usuario, id_rol), 
    FOREIGN KEY(id_rol) REFERENCES rol (id_rol) ON DELETE RESTRICT, 
    FOREIGN KEY(id_usuario) REFERENCES usuario (id_usuario) ON DELETE CASCADE
);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

