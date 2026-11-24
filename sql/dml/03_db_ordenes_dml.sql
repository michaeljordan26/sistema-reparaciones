-- =====================================================================
-- DML de ejemplo — db_ordenes (MS3) · puerto 5434 en su PC
-- =====================================================================

-- 1. Órdenes abiertas por estado y prioridad
SELECT estado_actual, prioridad, COUNT(*) AS ordenes
FROM orden_trabajo
WHERE estado_actual NOT IN ('ENTREGADO', 'CANCELADO')
GROUP BY estado_actual, prioridad
ORDER BY estado_actual, prioridad;

-- 2. Historial de una orden con su técnico asignado (JOIN)
SELECT o.id_orden, h.fecha_cambio, h.estado_anterior, h.estado_nuevo, h.observacion,
       a.nombre_tecnico
FROM orden_trabajo o
JOIN historial_estado h ON h.id_orden = o.id_orden
LEFT JOIN asignacion a ON a.id_orden = o.id_orden AND a.estado_asignacion = 'ACTIVA'
WHERE o.id_orden = 1
ORDER BY h.fecha_cambio;

-- 3. Carga de trabajo por técnico
SELECT a.nombre_tecnico, COUNT(*) AS ordenes_activas
FROM asignacion a
JOIN orden_trabajo o ON o.id_orden = a.id_orden
WHERE a.estado_asignacion = 'ACTIVA'
  AND o.estado_actual NOT IN ('ENTREGADO', 'CANCELADO')
GROUP BY a.nombre_tecnico
ORDER BY ordenes_activas DESC;

-- 4. Cambio de estado = UPDATE + INSERT en la misma transacción
BEGIN;
UPDATE orden_trabajo SET estado_actual = 'EN_DIAGNOSTICO' WHERE id_orden = 1 AND estado_actual = 'RECIBIDO';
INSERT INTO historial_estado (id_orden, estado_anterior, estado_nuevo, observacion, id_usuario)
VALUES (1, 'RECIBIDO', 'EN_DIAGNOSTICO', 'Ejemplo DML', 1);
SELECT id_orden, estado_actual FROM orden_trabajo WHERE id_orden = 1;
ROLLBACK;

-- 5. Solo puede haber UNA asignación ACTIVA por orden (índice único parcial)
DO $$
BEGIN
  INSERT INTO asignacion (id_orden, id_tecnico, id_usuario_tecnico, nombre_tecnico, estado_asignacion)
  SELECT id_orden, 99, 99, 'Técnico duplicado', 'ACTIVA' FROM asignacion WHERE estado_asignacion = 'ACTIVA' LIMIT 1;
  RAISE NOTICE 'No había asignaciones activas para probar';
EXCEPTION WHEN unique_violation THEN
  RAISE NOTICE 'UNIQUE parcial: %', SQLERRM;
END $$;
