-- MaruNails — Migración 003
-- Ejecutar en Supabase SQL Editor

-- Campos de seguridad en clientes_reservas
ALTER TABLE clientes_reservas ADD COLUMN IF NOT EXISTS es_recurrente BOOLEAN DEFAULT FALSE;
ALTER TABLE clientes_reservas ADD COLUMN IF NOT EXISTS alergias TEXT;
ALTER TABLE clientes_reservas ADD COLUMN IF NOT EXISTS bloqueado BOOLEAN DEFAULT FALSE;
ALTER TABLE clientes_reservas ADD COLUMN IF NOT EXISTS motivo_bloqueo TEXT;

-- Lista de espera
CREATE TABLE IF NOT EXISTS lista_espera (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_id BIGINT REFERENCES clientes_reservas(id) ON DELETE SET NULL,
    nombre TEXT,
    telefono TEXT,
    servicio_id BIGINT REFERENCES servicios(id) ON DELETE SET NULL,
    colaboradora_id BIGINT REFERENCES colaboradoras(id) ON DELETE SET NULL,
    fecha_preferida DATE,
    hora_preferida TIME,
    notas TEXT,
    estado TEXT DEFAULT 'activo',  -- activo | asignado | cancelado
    created_at TIMESTAMPTZ DEFAULT NOW()
);
