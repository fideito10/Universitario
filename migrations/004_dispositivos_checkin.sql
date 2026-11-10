-- 004: celulares vinculados a un DNI para el check-in por QR (asistencia).
-- En el celu queda un token aleatorio (cookie); aca solo se guarda su hash SHA-256.

CREATE TABLE dispositivos (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dni         text NOT NULL,
    token_hash  text NOT NULL UNIQUE,
    etiqueta    text,                          -- User-Agent resumido, para que el staff lo reconozca
    created_at  timestamptz NOT NULL DEFAULT now(),
    last_seen   timestamptz,
    revoked_at  timestamptz
);

CREATE INDEX idx_dispositivos_dni_activos ON dispositivos (dni) WHERE revoked_at IS NULL;
