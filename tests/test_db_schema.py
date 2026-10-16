"""Corre contra la DB real dentro de un schema temporal (no toca public)."""
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.db import connect  # noqa: E402
from src.data.migrate import apply_migrations, list_migrations  # noqa: E402

TABLES = {
    "usuarios", "jugadores", "wellness", "asistencias",
    "sheet_rows", "sheet_headers", "sync_runs", "schema_migrations",
}
INDEXES = {
    "idx_sheet_rows_source_dni", "idx_wellness_dni_fecha",
    "idx_asistencias_fecha_cat", "idx_asistencias_dni", "idx_sync_runs_source",
}


@pytest.fixture(scope="module")
def schema():
    name = "test_" + uuid.uuid4().hex[:10]
    with connect() as conn:
        first = apply_migrations(conn, schema=name)
        yield name, conn, first
        conn.rollback()
        conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{name}" CASCADE')
        conn.commit()


def test_applies_all_migrations(schema):
    _, _, first = schema
    assert first == [p.name for p in list_migrations()]


def test_idempotent(schema):
    name, conn, _ = schema
    assert apply_migrations(conn, schema=name) == []


def test_tables_and_indexes(schema):
    name, conn, _ = schema
    tables = {r[0] for r in conn.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname=:s"), {"s": name})}
    assert TABLES <= tables
    idx = {r[0] for r in conn.execute(
        text("SELECT indexname FROM pg_indexes WHERE schemaname=:s"), {"s": name})}
    assert INDEXES <= idx


def test_sheet_rows_roundtrip(schema):
    name, conn, _ = schema
    conn.exec_driver_sql(f'SET LOCAL search_path TO "{name}"')
    conn.exec_driver_sql(
        "INSERT INTO sheet_rows (source,row_num,dni,data) "
        "VALUES ('medica',1,'123','{\"Nombre\": \"x\"}')"
    )
    n = conn.execute(text("SELECT count(*) FROM sheet_rows WHERE source='medica'")).scalar()
    assert n == 1
    conn.rollback()
