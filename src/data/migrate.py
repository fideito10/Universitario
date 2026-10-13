"""Aplica migraciones SQL numeradas de migrations/ (idempotente).

Uso: python -m src.data.migrate
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from sqlalchemy import text

from src.data.db import connect

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
_NAME_RE = re.compile(r"^\d{3,}_.+\.sql$")
_LOCK_KEY = 727201  # advisory lock: evita migraciones concurrentes


def list_migrations() -> list[Path]:
    return sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if _NAME_RE.match(p.name))


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def apply_migrations(conn=None, schema: str | None = None) -> list[str]:
    """Aplica las pendientes y devuelve los nombres aplicados.

    Si ``schema`` se indica, crea el schema (si falta) y trabaja ahi.
    Todo el estado de sesion es local a la transaccion (SET LOCAL y locks
    xact) para ser seguro detras del pooler de Neon (pgbouncer).
    """
    own = conn is None
    if own:
        conn = connect()
    applied: list[str] = []

    def begin():
        # Inicia transaccion: lock global + search_path local.
        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _LOCK_KEY})
        if schema:
            conn.exec_driver_sql(f"CREATE SCHEMA IF NOT EXISTS {_quote_ident(schema)}")
            conn.exec_driver_sql(f"SET LOCAL search_path TO {_quote_ident(schema)}")

    try:
        begin()
        conn.exec_driver_sql(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        conn.commit()
        for path in list_migrations():
            begin()
            done = {r[0] for r in conn.execute(text("SELECT name FROM schema_migrations"))}
            if path.name in done:
                conn.rollback()
                continue
            conn.exec_driver_sql(path.read_text(encoding="utf-8"))
            conn.execute(
                text("INSERT INTO schema_migrations (name) VALUES (:n)"), {"n": path.name}
            )
            conn.commit()  # cada migracion en su propia transaccion
            applied.append(path.name)
    except Exception:
        conn.rollback()
        raise
    finally:
        if own:
            conn.close()
    return applied


def main() -> int:
    applied = apply_migrations()
    if applied:
        for name in applied:
            print(f"aplicada: {name}")
    else:
        print("sin migraciones pendientes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
