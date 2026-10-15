-- MaruNails — «¿Cómo nos conociste?» guardado en la clienta (no en el turno)
-- Ejecutar en Supabase SQL Editor ANTES de deployar el código que lo usa.
-- Idempotente: se puede correr más de una vez.
-- Valores: instagram | google_maps | meta_ads | recomendacion | paso_por_el_local | otro (NULL = sin dato)

ALTER TABLE clientes_reservas ADD COLUMN IF NOT EXISTS origen TEXT;
