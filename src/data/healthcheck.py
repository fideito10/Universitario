"""Chequeo de conectividad y estado del esquema.

Uso: python -m src.data.healthcheck
"""
from __future__ import annotations

import sys

from sqlalchemy import text

from src.data.db import connect

TABLES = [
    "usuarios", "jugadores", "wellness", "asistencias",
    "sheet_rows", "sheet_headers", "sync_runs",
]


def main() -> int:
    try:
        with connect() as conn:
            print("conexion: OK")
            print("version:", conn.execute(text("SELECT version()")).scalar())
            exists = conn.execute(text("SELECT to_regclass('schema_migrations')")).scalar()
            if not exists:
                print("migraciones: ninguna (correr python -m src.data.migrate)")
                return 1
            print("migraciones aplicadas:")
            for name, at in conn.execute(
                text("SELECT name, applied_at FROM schema_migrations ORDER BY name")
            ):
                print(f"  {name}  ({at:%Y-%m-%d %H:%M})")
            print("filas por tabla:")
            for t in TABLES:
                if conn.execute(text("SELECT to_regclass(:t)"), {"t": t}).scalar():
                    n = conn.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                    print(f"  {t}: {n}")
                else:
                    print(f"  {t}: (falta)")
        return 0
    except Exception as exc:  # no imprimir detalle: podria incluir la URL
        print(f"conexion: FALLO ({type(exc).__name__})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
