-- =====================================================================
-- DML de ejemplo — db_clientes (MS2) · puerto 5433 en su PC
-- Ejecute cada bloque con Ctrl+Enter en DBeaver, o todo el script con Alt+X.
-- El bloque 2 termina en ROLLBACK: muestra los cambios y luego los deshace.
-- Cambie ROLLBACK por COMMIT si quiere guardarlos.
-- =====================================================================

-- 1. CONSULTAS (READ) ----------------------------------------------------
-- 1.1 Clientes activos con cuántos equipos tiene cada uno (JOIN + GROUP BY)
SELECT c.id_cliente,
       c.nombres || ' ' || c.apellidos AS cliente,
       c.tipo_documento || ' ' || c.numero_documento AS documento,
       COUNT(e.id_equipo) AS equipos
FROM cliente c
LEFT JOIN equipo e ON e.id_cliente = c.id_cliente AND e.estado = 'ACTIVO'
WHERE c.estado = 'ACTIVO'
GROUP BY c.id_cliente
ORDER BY equipos DESC, cliente;

-- 1.2 Equipos por tipo y marca
SELECT tipo_equipo, marca, COUNT(*) AS cantidad
FROM equipo
GROUP BY tipo_equipo, marca
ORDER BY cantidad DESC;

-- 2. TRANSACCIÓN CON INSERT, UPDATE Y DELETE ------------------------------
BEGIN;

INSERT INTO cliente (tipo_documento, numero_documento, nombres, apellidos, telefono, correo, estado)
VALUES ('CC', '1022334455', 'Laura', 'Gómez Ruiz', '3104567890', 'laura.gomez@correo.com', 'ACTIVO');

INSERT INTO equipo (id_cliente, tipo_equipo, marca, modelo, numero_serie, descripcion, estado)
VALUES (currval('cliente_id_cliente_seq'), 'PORTATIL', 'Asus', 'VivoBook 15', 'ASU-DML-0001',
        'Portátil gris, cargador original', 'ACTIVO');

UPDATE cliente SET telefono = '3209998877'
WHERE numero_documento = '1022334455';

SELECT c.nombres, c.telefono, e.marca, e.modelo, e.numero_serie
FROM cliente c JOIN equipo e ON e.id_cliente = c.id_cliente
WHERE c.numero_documento = '1022334455';

DELETE FROM equipo WHERE numero_serie = 'ASU-DML-0001';

ROLLBACK;   -- deshace todo el bloque (atomicidad)

-- 3. LAS RESTRICCIONES PROTEGEN LOS DATOS ----------------------------------
-- Cada intento falla a propósito; el mensaje aparece en la pestaña "Salida".
DO $$
BEGIN
  BEGIN  -- llave foránea con ON DELETE RESTRICT: no se borra un cliente con equipos
    DELETE FROM cliente WHERE id_cliente = (SELECT id_cliente FROM equipo LIMIT 1);
  EXCEPTION WHEN foreign_key_violation THEN
    RAISE NOTICE 'FK RESTRICT: %', SQLERRM;
  END;
  BEGIN  -- UNIQUE (tipo_documento, numero_documento)
    INSERT INTO cliente (tipo_documento, numero_documento, nombres, apellidos, telefono, estado)
    SELECT tipo_documento, numero_documento, 'Copia', 'Duplicada', '3000000000', 'ACTIVO'
    FROM cliente LIMIT 1;
  EXCEPTION WHEN unique_violation THEN
    RAISE NOTICE 'UNIQUE: %', SQLERRM;
  END;
  BEGIN  -- CHECK sobre el tipo de documento
    INSERT INTO cliente (tipo_documento, numero_documento, nombres, apellidos, telefono, estado)
    VALUES ('XX', '999', 'Tipo', 'Inválido', '3000000000', 'ACTIVO');
  EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'CHECK: %', SQLERRM;
  END;
END $$;
