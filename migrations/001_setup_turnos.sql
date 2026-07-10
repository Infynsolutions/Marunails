-- MaruNails — Sistema de Turnos
-- Ejecutar en Supabase SQL Editor

-- Servicios
CREATE TABLE IF NOT EXISTS servicios (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    descripcion TEXT,
    precio_desde INTEGER NOT NULL,
    precio_hasta INTEGER,
    duracion_min INTEGER NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    orden INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Colaboradoras
CREATE TABLE IF NOT EXISTS colaboradoras (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL,
    rol TEXT,
    foto_url TEXT,
    activa BOOLEAN DEFAULT TRUE,
    comision DECIMAL(3,2) DEFAULT 0.40,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Qué servicios puede hacer cada colaboradora
CREATE TABLE IF NOT EXISTS colaboradora_servicios (
    colaboradora_id BIGINT REFERENCES colaboradoras(id) ON DELETE CASCADE,
    servicio_id BIGINT REFERENCES servicios(id) ON DELETE CASCADE,
    PRIMARY KEY (colaboradora_id, servicio_id)
);

-- Disponibilidad semanal (horario recurrente)
CREATE TABLE IF NOT EXISTS disponibilidad (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    colaboradora_id BIGINT REFERENCES colaboradoras(id) ON DELETE CASCADE,
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),  -- 0=lunes, 6=domingo
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL
);

-- Bloqueos específicos (días libres, vacaciones, etc.)
CREATE TABLE IF NOT EXISTS bloqueos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    colaboradora_id BIGINT REFERENCES colaboradoras(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    hora_inicio TIME,
    hora_fin TIME,
    motivo TEXT,
    todo_el_dia BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Clientes (para reservas públicas)
CREATE TABLE IF NOT EXISTS clientes_reservas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT,
    telefono TEXT NOT NULL,
    email TEXT,
    idioma TEXT DEFAULT 'es',
    fecha_nacimiento DATE,
    notas TEXT,
    acepto_politicas BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Turnos / Reservas
CREATE TABLE IF NOT EXISTS turnos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_id BIGINT REFERENCES clientes_reservas(id),
    colaboradora_id BIGINT REFERENCES colaboradoras(id),
    servicio_id BIGINT REFERENCES servicios(id),
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado TEXT DEFAULT 'pendiente',
    precio INTEGER,
    notas TEXT,
    notas_internas TEXT,
    canal TEXT DEFAULT 'web',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
