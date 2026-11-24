-- =====================================================================
-- DML de ejemplo — db_inventario (MS5) · puerto 5436 en su PC
-- =====================================================================

-- 1. CONSULTAS -----------------------------------------------------------
-- 1.1 Repuestos con stock bajo (stock_actual <= stock_minimo)
SELECT codigo, nombre, stock_actual, stock_minimo
FROM repuesto
WHERE activo AND stock_actual <= stock_minimo
ORDER BY stock_actual;

-- 1.2 Valor del inventario por categoría
SELECT categoria,
       SUM(stock_actual)                AS unidades,
       SUM(stock_actual * precio_costo) AS valor_costo
FROM repuesto
WHERE activo
GROUP BY categoria
ORDER BY valor_costo DESC;

-- 1.3 Kárdex: últimos movimientos con el repuesto (JOIN)
SELECT m.fecha, r.codigo, m.tipo, m.cantidad, m.stock_anterior, m.stock_resultante, m.id_orden
FROM movimiento_inventario m
JOIN repuesto r ON r.id_repuesto = m.id_repuesto
ORDER BY m.fecha DESC
LIMIT 20;

-- 2. TRANSACCIÓN OLTP: SALIDA DE UN REPUESTO -----------------------------
-- Es lo mismo que hace MS5 en POST /repuestos/{id}/salidas.
BEGIN;

SELECT id_repuesto, stock_actual
FROM repuesto WHERE codigo = 'PASTA-TERM'
FOR UPDATE;              -- bloquea la fila: otra salida simultánea espera aquí

INSERT INTO movimiento_inventario (id_repuesto, tipo, cantidad, stock_anterior, stock_resultante,
                                   precio_unitario, id_orden, motivo, id_usuario)
SELECT id_repuesto, 'SALIDA', 2, stock_actual, stock_actual - 2, precio_venta, 1,
       'Ejemplo DML: uso en reparación', 1
FROM repuesto WHERE codigo = 'PASTA-TERM';

UPDATE repuesto SET stock_actual = stock_actual - 2 WHERE codigo = 'PASTA-TERM';

SELECT codigo, stock_actual FROM repuesto WHERE codigo = 'PASTA-TERM';

ROLLBACK;   -- cambie por COMMIT para guardar la salida

-- 3. EL STOCK NUNCA QUEDA NEGATIVO ----------------------------------------
DO $$
BEGIN
  UPDATE repuesto SET stock_actual = stock_actual - 1000 WHERE codigo = 'TECL-HP-15';
EXCEPTION WHEN check_violation THEN
  RAISE NOTICE 'CHECK stock_actual >= 0: %', SQLERRM;
END $$;
