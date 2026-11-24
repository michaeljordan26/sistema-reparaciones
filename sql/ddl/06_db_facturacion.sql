

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE presupuesto (
    id_presupuesto SERIAL NOT NULL, 
    id_orden INTEGER NOT NULL, 
    fecha DATE DEFAULT CURRENT_DATE NOT NULL, 
    fecha_vencimiento DATE NOT NULL, 
    subtotal_materiales NUMERIC(12, 2) NOT NULL, 
    subtotal_mano_obra NUMERIC(12, 2) NOT NULL, 
    subtotal NUMERIC(12, 2) NOT NULL, 
    iva_porcentaje INTEGER NOT NULL, 
    iva NUMERIC(12, 2) NOT NULL, 
    total NUMERIC(12, 2) NOT NULL, 
    observaciones VARCHAR(500), 
    estado VARCHAR(10) NOT NULL, 
    id_usuario INTEGER NOT NULL, 
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id_presupuesto), 
    CONSTRAINT ck_presupuesto_estado CHECK (estado IN ('PENDIENTE','APROBADO','RECHAZADO','ANULADO')), 
    CONSTRAINT ck_presupuesto_vencimiento CHECK (fecha_vencimiento >= fecha), 
    CONSTRAINT ck_presupuesto_total CHECK (total = subtotal + iva)
);

CREATE INDEX ix_presupuesto_id_orden ON presupuesto (id_orden);

CREATE UNIQUE INDEX uq_presupuesto_vigente ON presupuesto (id_orden) WHERE estado IN ('PENDIENTE','APROBADO');

CREATE TABLE detalle_presupuesto (
    id_detalle SERIAL NOT NULL, 
    id_presupuesto INTEGER NOT NULL, 
    tipo VARCHAR(10) NOT NULL, 
    id_repuesto INTEGER, 
    descripcion VARCHAR(200) NOT NULL, 
    cantidad NUMERIC(8, 2) NOT NULL, 
    precio_unitario NUMERIC(12, 2) NOT NULL, 
    subtotal NUMERIC(12, 2) NOT NULL, 
    PRIMARY KEY (id_detalle), 
    CONSTRAINT ck_detalle_repuesto CHECK ((tipo = 'REPUESTO') = (id_repuesto IS NOT NULL)), 
    CONSTRAINT ck_detalle_tipo CHECK (tipo IN ('MANO_OBRA','REPUESTO')), 
    CONSTRAINT ck_detalle_cantidad CHECK (cantidad > 0), 
    CONSTRAINT ck_detalle_precio CHECK (precio_unitario >= 0), 
    CONSTRAINT ck_detalle_subtotal CHECK (subtotal = round(cantidad * precio_unitario, 2)), 
    FOREIGN KEY(id_presupuesto) REFERENCES presupuesto (id_presupuesto) ON DELETE CASCADE
);

CREATE INDEX ix_detalle_presupuesto_id_presupuesto ON detalle_presupuesto (id_presupuesto);

CREATE TABLE factura (
    id_factura SERIAL NOT NULL, 
    id_orden INTEGER NOT NULL, 
    id_presupuesto INTEGER NOT NULL, 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    subtotal_materiales NUMERIC(12, 2) NOT NULL, 
    subtotal_mano_obra NUMERIC(12, 2) NOT NULL, 
    subtotal NUMERIC(12, 2) NOT NULL, 
    iva_porcentaje INTEGER NOT NULL, 
    iva NUMERIC(12, 2) NOT NULL, 
    total NUMERIC(12, 2) NOT NULL, 
    anulada BOOLEAN NOT NULL, 
    motivo_anulacion VARCHAR(300), 
    id_usuario INTEGER NOT NULL, 
    PRIMARY KEY (id_factura), 
    CONSTRAINT ck_factura_total CHECK (total = subtotal + iva), 
    CONSTRAINT ck_factura_total_positivo CHECK (total >= 0), 
    FOREIGN KEY(id_presupuesto) REFERENCES presupuesto (id_presupuesto) ON DELETE RESTRICT
);

CREATE INDEX ix_factura_id_orden ON factura (id_orden);

CREATE UNIQUE INDEX uq_factura_activa ON factura (id_orden) WHERE anulada = false;

CREATE TABLE respuesta_presupuesto (
    id_respuesta SERIAL NOT NULL, 
    id_presupuesto INTEGER NOT NULL, 
    decision VARCHAR(10) NOT NULL, 
    medio VARCHAR(12) NOT NULL, 
    nombre_responde VARCHAR(120) NOT NULL, 
    observacion VARCHAR(500), 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    id_usuario INTEGER NOT NULL, 
    PRIMARY KEY (id_respuesta), 
    CONSTRAINT ck_respuesta_decision CHECK (decision IN ('APROBADO','RECHAZADO')), 
    CONSTRAINT ck_respuesta_medio CHECK (medio IN ('PRESENCIAL','TELEFONO','CORREO','WHATSAPP')), 
    FOREIGN KEY(id_presupuesto) REFERENCES presupuesto (id_presupuesto) ON DELETE RESTRICT, 
    UNIQUE (id_presupuesto)
);

CREATE TABLE detalle_factura (
    id_detalle SERIAL NOT NULL, 
    id_factura INTEGER NOT NULL, 
    tipo VARCHAR(10) NOT NULL, 
    id_repuesto INTEGER, 
    descripcion VARCHAR(200) NOT NULL, 
    cantidad NUMERIC(8, 2) NOT NULL, 
    precio_unitario NUMERIC(12, 2) NOT NULL, 
    subtotal NUMERIC(12, 2) NOT NULL, 
    PRIMARY KEY (id_detalle), 
    CONSTRAINT ck_detfac_tipo CHECK (tipo IN ('MANO_OBRA','REPUESTO')), 
    CONSTRAINT ck_detfac_cantidad CHECK (cantidad > 0), 
    CONSTRAINT ck_detfac_subtotal CHECK (subtotal = round(cantidad * precio_unitario, 2)), 
    FOREIGN KEY(id_factura) REFERENCES factura (id_factura) ON DELETE CASCADE
);

CREATE INDEX ix_detalle_factura_id_factura ON detalle_factura (id_factura);

CREATE TABLE pago (
    id_pago SERIAL NOT NULL, 
    id_factura INTEGER NOT NULL, 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    monto NUMERIC(12, 2) NOT NULL, 
    metodo VARCHAR(15) NOT NULL, 
    referencia VARCHAR(60), 
    tipo VARCHAR(10) NOT NULL, 
    saldo_anterior NUMERIC(12, 2) NOT NULL, 
    saldo_resultante NUMERIC(12, 2) NOT NULL, 
    anulado BOOLEAN NOT NULL, 
    motivo_anulacion VARCHAR(300), 
    id_usuario INTEGER NOT NULL, 
    PRIMARY KEY (id_pago), 
    CONSTRAINT ck_pago_referencia CHECK (metodo = 'EFECTIVO' OR referencia IS NOT NULL), 
    CONSTRAINT ck_pago_metodo CHECK (metodo IN ('EFECTIVO','TARJETA','TRANSFERENCIA','NEQUI','DAVIPLATA')), 
    CONSTRAINT ck_pago_tipo CHECK (tipo IN ('ABONO','PAGO_TOTAL')), 
    CONSTRAINT ck_pago_monto CHECK (monto > 0), 
    FOREIGN KEY(id_factura) REFERENCES factura (id_factura) ON DELETE RESTRICT
);

CREATE INDEX ix_pago_fecha ON pago (fecha);

CREATE INDEX ix_pago_id_factura ON pago (id_factura);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

