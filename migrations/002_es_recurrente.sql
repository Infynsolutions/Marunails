-- Agrega campo es_recurrente a clientes_reservas
ALTER TABLE clientes_reservas ADD COLUMN IF NOT EXISTS es_recurrente BOOLEAN DEFAULT FALSE;
