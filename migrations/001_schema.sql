-- 001: esquema inicial (ver docs/MIGRACION_DB.md seccion 4)

-- Datos propios de la app
CREATE TABLE usuarios (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario     text NOT NULL UNIQUE,
    clave_hash  text,
    rol         text,
    nombre      text,
    dni         text,
    email       text,
    activo      boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE jugadores (
    dni         text PRIMARY KEY,   -- normalizado: solo digitos
    nombre      text,
    apellido    text,
    categoria   text,
    posicion    text,
    estado      text,
    extra       jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE wellness (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dni         text NOT NULL,
    fecha       date,
    rpe         numeric,
    sueno       numeric,
    doms        numeric,
    score       numeric,
    nombre      text,
    email       text,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE asistencias (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha       date,
    categoria   text,
    dni         text,
    jugador     text,
    estado      text,
    extra       jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Espejo de fuentes externas / formularios
CREATE TABLE sheet_rows (
    source      text NOT NULL,      -- 'medica' | 'nutricion' | 'fisica_base_test' | 'partido:<pestana>'
    row_num     integer NOT NULL,   -- posicion en la hoja (preserva el orden)
    row_hash    text,               -- sha1 de la fila (upsert idempotente)
    dni         text,
    fecha       date,
    data        jsonb NOT NULL,     -- {header_original: valor_string}
    synced_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source, row_num)
);

CREATE TABLE sheet_headers (
    source      text PRIMARY KEY,
    headers     jsonb NOT NULL,     -- orden original de columnas
    synced_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sync_runs (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source      text NOT NULL,
    started_at  timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    rows        integer,
    status      text,
    error       text
);

-- Indices (jugadores(dni) ya esta indexado por la PK)
CREATE INDEX idx_sheet_rows_source_dni ON sheet_rows (source, dni);
CREATE INDEX idx_wellness_dni_fecha    ON wellness (dni, fecha);
CREATE INDEX idx_asistencias_fecha_cat ON asistencias (fecha, categoria);
CREATE INDEX idx_asistencias_dni       ON asistencias (dni);
CREATE INDEX idx_sync_runs_source      ON sync_runs (source, started_at DESC);
