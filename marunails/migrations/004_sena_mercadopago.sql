-- MaruNails — Seña de reserva con Mercado Pago
-- Ejecutar en Supabase SQL Editor ANTES de deployar el código que la usa.
-- Idempotente: se puede correr más de una vez.

CREATE TABLE IF NOT EXISTS pagos_sena (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    token UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,  -- va en la URL pública de resultado (no exponer el id secuencial)
    cliente_id BIGINT REFERENCES clientes_reservas(id),
    monto INTEGER NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',  -- pendiente | aprobado | rechazado | reembolsado
    mp_preference_id TEXT,
    mp_payment_id TEXT UNIQUE,
    pagado_at TIMESTAMPTZ,
    reembolsado_at TIMESTAMPTZ,
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE turnos ADD COLUMN IF NOT EXISTS pago_sena_id BIGINT REFERENCES pagos_sena(id);

CREATE INDEX IF NOT EXISTS turnos_pago_sena_id_idx ON turnos (pago_sena_id);
