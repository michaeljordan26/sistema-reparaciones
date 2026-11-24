-- =====================================================================
-- Creación del usuario y las 7 bases de datos (una por microservicio)
-- Solo para una instalación SIN Docker y con UN solo PostgreSQL.
-- Con Docker Compose no hace falta: cada contenedor crea su base.
-- Ejecutar como superusuario (postgres).
-- =====================================================================
CREATE USER taller WITH PASSWORD 'taller123';   -- cambie la contraseña fuera del entorno académico

CREATE DATABASE db_usuarios     OWNER taller ENCODING 'UTF8';
CREATE DATABASE db_clientes     OWNER taller ENCODING 'UTF8';
CREATE DATABASE db_ordenes      OWNER taller ENCODING 'UTF8';
CREATE DATABASE db_reparaciones OWNER taller ENCODING 'UTF8';
CREATE DATABASE db_inventario   OWNER taller ENCODING 'UTF8';
CREATE DATABASE db_facturacion  OWNER taller ENCODING 'UTF8';
CREATE DATABASE db_reportes     OWNER taller ENCODING 'UTF8';
