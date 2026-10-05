-- MaruNails — Cierra todas las tablas a la key anon.
-- La key anon estaba en el repo (público) y con ella se podían leer clientas, cortes, gastos y turnos.
-- El navegador nunca habla con Supabase: solo el server, que desde ahora usa la service key (bypassea RLS).
-- Ejecutar en Supabase SQL Editor DESPUÉS de que esté deployado el código que usa la service key.
-- Idempotente: se puede correr más de una vez.

DO $$
DECLARE
    r record;
BEGIN
    -- RLS prendido en todas las tablas del schema public
    FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', r.tablename);
    END LOOP;

    -- Sin políticas: nada de lo que dejaba leer/escribir a anon o authenticated
    FOR r IN SELECT policyname, tablename FROM pg_policies WHERE schemaname = 'public' LOOP
        EXECUTE format('DROP POLICY %I ON public.%I', r.policyname, r.tablename);
    END LOOP;
END $$;

-- Además, sin permisos de tabla para los roles públicos (también vistas y secuencias)
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES    FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;

-- Verificación: tiene que devolver 0 filas
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND NOT rowsecurity
UNION ALL
SELECT tablename FROM pg_policies WHERE schemaname = 'public';
