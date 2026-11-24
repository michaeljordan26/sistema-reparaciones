
-- 1. Operaciones por microservicio en las últimas 24 horas
SELECT servicio, COUNT(*) AS operaciones,
       COUNT(*) FILTER (WHERE NOT exito) AS fallidas
FROM registro_auditoria
WHERE fecha >= now() - interval '24 hours'
GROUP BY servicio
ORDER BY operaciones DESC;

-- 2. Últimos accesos denegados (403)
SELECT fecha, servicio, metodo, ruta, id_usuario, roles
FROM registro_auditoria
WHERE codigo_estado = 403
ORDER BY fecha DESC
LIMIT 10;

-- 3. Notificaciones enviadas a los clientes
SELECT id_orden, tipo, canal, destinatario, estado, fecha
FROM notificacion
ORDER BY fecha DESC
LIMIT 10;

-- 4. La auditoría es inmutable: el trigger bloquea UPDATE y DELETE
DO $$
BEGIN
  DELETE FROM registro_auditoria;
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'Trigger tg_auditoria_inmutable: %', SQLERRM;
END $$;
