"""Escrituras directas a sheet_rows (reportes cargados desde la app).

`insertar_fila` inserta UNA fila en `sheet_rows` para una fuente de formulario
(`medica` o `nutricion`) con `row_num >= APP_ROW_BASE`, de modo que el sync
(Sheets -> DB) nunca la borra y `repo.*` la devuelve al final, ordenada por row_num.

- Transaccional y sin estado de sesion: usa `pg_advisory_xact_lock` (compatible con
  pgbouncer) para serializar el calculo de `row_num` por fuente.
- `data` usa las claves unicas de `sheet_headers` (mismas que escribe el sync).
- `mirrored_at`: epoch de cuando la misma fila se agrego tambien al Sheet (espejo).
  El sync borra la copia local una vez que ya trajo la fila desde Sheets (evita duplicados).
"""
from __future__ import annotations

import json

from sqlalchemy import text

from src.data.db import connect
from src.data.rows import (
    APP_ROW_BASE, clean_text, find_dni_index, find_fecha_index, normalize_dni,
    parse_fecha, row_hash, unique_keys,
)

SOURCES_ESCRIBIBLES = ("medica", "nutricion")

# Si los headers del Sheet no permiten ubicar DNI/fecha (p.ej. la hoja medica tiene
# headers genericos "Columna N"), posicion de cada dato en el reporte que arma la app.
_POS_DEFAULT = {
    "medica": {"dni": 4, "fecha": 0},
    "nutricion": {"dni": 2, "fecha": 0},
}

_INSERT = text("""
INSERT INTO sheet_rows (source, row_num, row_hash, dni, fecha, data, synced_at)
SELECT :source,
       GREATEST(COALESCE(MAX(row_num), :base - 1), :base - 1) + 1,
       :row_hash, :dni, CAST(:fecha AS date), CAST(:data AS jsonb), now()
FROM sheet_rows WHERE source = :source
RETURNING row_num
""")


def _headers(conn, source: str) -> list[str]:
    h = conn.execute(text("SELECT headers FROM sheet_headers WHERE source = :s"),
                     {"s": source}).scalar()
    if not h:
        raise RuntimeError(f"La fuente '{source}' no tiene headers sincronizados todavia.")
    return list(h)


def _insert(conn, source: str, headers: list[str], values: list[str], dni, fecha,
            mirrored_at: float | None) -> int:
    keys = unique_keys(headers)
    row = [clean_text(str(v)) for v in values]
    row = (row + [""] * len(headers))[:len(headers)]
    data = dict(zip(keys, row))
    if mirrored_at is not None:
        data["__mirrored__"] = repr(float(mirrored_at))
    pos = _POS_DEFAULT.get(source, {})
    if dni is None:
        i = find_dni_index(headers)
        i = pos.get("dni") if i is None else i
        dni = row[i] if i is not None and i < len(row) else None
    if fecha is None:
        i = find_fecha_index(headers)
        i = pos.get("fecha") if i is None else i
        fecha = row[i] if i is not None and i < len(row) else None
    conn.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"ins:{source}"})
    return conn.execute(_INSERT, {
        "source": source, "base": APP_ROW_BASE,
        "row_hash": row_hash(headers, row),
        "dni": normalize_dni(dni), "fecha": parse_fecha(fecha),
        "data": json.dumps(data, ensure_ascii=False),
    }).scalar()


def _run(source, build, conn):
    if source not in SOURCES_ESCRIBIBLES:
        raise ValueError(f"fuente no escribible: {source}")
    if conn is not None:  # el llamador maneja la transaccion
        return _insert(conn, source, *build(_headers(conn, source)))
    with connect() as c:
        n = _insert(c, source, *build(_headers(c, source)))
        c.commit()
        return n


def insertar_fila(source: str, valores_por_header: dict, *, dni=None, fecha=None,
                  mirrored_at: float | None = None, conn=None) -> int:
    """Inserta una fila indicando el valor por header original. Devuelve el row_num.

    Los headers no informados quedan en ''. Los headers desconocidos se rechazan.
    `conn`: conexion existente (el llamador hace commit/rollback); si es None abre una
    y confirma.
    """
    def build(headers):
        extra = [k for k in valores_por_header if k not in headers]
        if extra:
            raise ValueError(f"headers desconocidos para '{source}': {extra}")
        values = [str(valores_por_header.get(h, "")) for h in headers]
        return headers, values, dni, fecha, mirrored_at

    return _run(source, build, conn)


def insertar_fila_posicional(source: str, valores: list, *, dni=None, fecha=None,
                             mirrored_at: float | None = None, conn=None) -> int:
    """Igual que `append_row`: el valor i va a la columna i del Sheet."""
    def build(headers):
        return headers, [str(v) for v in valores], dni, fecha, mirrored_at

    return _run(source, build, conn)
