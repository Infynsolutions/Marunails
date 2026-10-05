-- MaruNails — Agenda del equipo (login por PIN + registro de cambios de turnos)
-- Ejecutar en Supabase SQL Editor. Idempotente: se puede correr más de una vez.
-- Ambas tablas tienen RLS sin políticas: solo se acceden desde el server con la service key.

-- PIN de cada colaboradora (separado de `colaboradoras`, que se lee con la key anon)
CREATE TABLE IF NOT EXISTS equipo_acceso (
    colaboradora_id BIGINT PRIMARY KEY REFERENCES colaboradoras(id) ON DELETE CASCADE,
    pin_hash TEXT NOT NULL,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE equipo_acceso ENABLE ROW LEVEL SECURITY;

-- Quién creó, movió o cambió cada turno
CREATE TABLE IF NOT EXISTS turno_cambios (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    turno_id BIGINT REFERENCES turnos(id) ON DELETE CASCADE,
    autor TEXT NOT NULL,                     -- 'Admin' o nombre de la colaboradora
    autor_colaboradora_id BIGINT REFERENCES colaboradoras(id) ON DELETE SET NULL,
    accion TEXT NOT NULL,                    -- creado | movido | editado | estado
    detalle TEXT NOT NULL,
    antes JSONB,
    despues JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE turno_cambios ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS turno_cambios_turno_id_idx ON turno_cambios (turno_id);
