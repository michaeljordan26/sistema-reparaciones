

BEGIN;

-- 1. Presupuesto con sus detalles (materiales + mano de obra)
INSERT INTO presupuesto (id_orden, fecha, fecha_vencimiento, subtotal_materiales, subtotal_mano_obra,
                         subtotal, iva_porcentaje, iva, total, estado, id_usuario)
VALUES (999, CURRENT_DATE, CURRENT_DATE + 15, 95000, 60000, 155000, 19, 29450, 184450, 'PENDIENTE', 1);

INSERT INTO detalle_presupuesto (id_presupuesto, tipo, id_repuesto, descripcion, cantidad, precio_unitario, subtotal)
VALUES (currval('presupuesto_id_presupuesto_seq'), 'REPUESTO', 1, 'Memoria RAM DDR4 8 GB', 1, 95000, 95000),
       (currval('presupuesto_id_presupuesto_seq'), 'MANO_OBRA', NULL, 'Instalación y pruebas', 1, 60000, 60000);

-- 2. El cliente aprueba
UPDATE presupuesto SET estado = 'APROBADO' WHERE id_orden = 999;

-- 3. Factura a partir del presupuesto aprobado
INSERT INTO factura (id_orden, id_presupuesto, subtotal_materiales, subtotal_mano_obra, subtotal,
                     iva_porcentaje, iva, total, anulada, id_usuario)
SELECT id_orden, id_presupuesto, subtotal_materiales, subtotal_mano_obra, subtotal,
       iva_porcentaje, iva, total, false, 1
FROM presupuesto WHERE id_orden = 999;

-- 4. Dos abonos (el segundo deja el saldo en 0)
INSERT INTO pago (id_factura, monto, metodo, referencia, tipo, saldo_anterior, saldo_resultante, anulado, id_usuario)
VALUES (currval('factura_id_factura_seq'), 100000, 'EFECTIVO', NULL, 'ABONO', 184450, 84450, false, 1),
       (currval('factura_id_factura_seq'), 84450, 'NEQUI', 'NEQ-778899', 'PAGO_TOTAL', 84450, 0, false, 1);

-- 5. Consulta: factura con total pagado y saldo (JOIN + agregación)
SELECT f.id_factura, f.id_orden, f.total,
       COALESCE(SUM(p.monto) FILTER (WHERE NOT p.anulado), 0)           AS pagado,
       f.total - COALESCE(SUM(p.monto) FILTER (WHERE NOT p.anulado), 0) AS saldo
FROM factura f
LEFT JOIN pago p ON p.id_factura = f.id_factura
WHERE f.id_orden = 999
GROUP BY f.id_factura;

-- 6. Las reglas también viven en la base de datos
DO $$
BEGIN
  BEGIN  -- total debe ser subtotal + iva
    UPDATE presupuesto SET total = 1 WHERE id_orden = 999;
  EXCEPTION WHEN check_violation THEN RAISE NOTICE 'CHECK total: %', SQLERRM; END;
  BEGIN  -- un pago por transferencia necesita referencia
    INSERT INTO pago (id_factura, monto, metodo, tipo, saldo_anterior, saldo_resultante, anulado, id_usuario)
    VALUES (currval('factura_id_factura_seq'), 1000, 'TRANSFERENCIA', 'ABONO', 0, 0, false, 1);
  EXCEPTION WHEN check_violation THEN RAISE NOTICE 'CHECK referencia: %', SQLERRM; END;
  BEGIN  -- no se borra una factura que tiene pagos
    DELETE FROM factura WHERE id_orden = 999;
  EXCEPTION WHEN foreign_key_violation THEN RAISE NOTICE 'FK RESTRICT: %', SQLERRM; END;
END $$;

ROLLBACK;
