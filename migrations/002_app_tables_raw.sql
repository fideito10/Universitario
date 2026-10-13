-- 002: tablas de la app preservan la fila cruda del Sheet (import unico, Fase 2).
-- Jugadores_Maestro tiene DNIs duplicados/vacios: el DNI deja de ser PK.

ALTER TABLE jugadores DROP CONSTRAINT jugadores_pkey;
ALTER TABLE jugadores ALTER COLUMN dni DROP NOT NULL;
ALTER TABLE jugadores ADD COLUMN id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY;
ALTER TABLE jugadores ADD COLUMN orden integer;
CREATE INDEX idx_jugadores_dni ON jugadores (dni);

-- clave_hash guarda hoy la clave en texto; clave_es_hash=false lo marca (re-hash en Fase 4).
ALTER TABLE usuarios ADD COLUMN clave_es_hash boolean NOT NULL DEFAULT false;
ALTER TABLE usuarios ADD COLUMN orden integer;
ALTER TABLE usuarios ADD COLUMN extra jsonb NOT NULL DEFAULT '{}'::jsonb;

-- Wellness_Jugador no trae DNI (identifica por Nombre_Jugador/Email_Jugador).
ALTER TABLE wellness ALTER COLUMN dni DROP NOT NULL;
ALTER TABLE wellness ADD COLUMN orden integer;
ALTER TABLE wellness ADD COLUMN extra jsonb NOT NULL DEFAULT '{}'::jsonb;
