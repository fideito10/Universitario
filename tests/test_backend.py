"""Fase 3: backend Postgres detras de DATA_BACKEND.

- Paridad de cada loader modificado: DATA_BACKEND=sheets (Google en vivo, solo lectura)
  vs DATA_BACKEND=postgres. Requiere credenciales de Google + DATABASE_URL + DB sincronizada.
- Fallback ante DB caida (DATABASE_URL invalida).
- Escritura (insertar_fila) y limpieza de espejo en un schema temporal; no toca `public`.
Las diferencias se reportan solo con indices/columnas, nunca con valores.
"""
import sys
import time
import uuid
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_parity import _have_db, _have_google, diff_frames, diff_rows  # noqa: E402

from src.data import backend, sources as S  # noqa: E402
from src.data.rows import APP_ROW_BASE  # noqa: E402

needs_live = pytest.mark.skipif(
    not (_have_google() and _have_db()),
    reason="requiere credenciales de Google y DATABASE_URL",
)
needs_db = pytest.mark.skipif(not _have_db(), reason="requiere DATABASE_URL")

MEDICA, NUTRI, FISICA = S.sheet_id("medica"), S.sheet_id("nutricion"), S.sheet_id("fisica")
TAB_NUTRI, TAB_FISICA = S.tab_name("nutricion"), S.tab_name("fisica")


def _modo(monkeypatch, valor):
    import streamlit as st
    monkeypatch.setenv("DATA_BACKEND", valor)
    backend.reset_caida()
    st.cache_data.clear()


@pytest.fixture(autouse=True)
def _limpio():
    import streamlit as st
    yield
    backend.reset_caida()
    st.cache_data.clear()


def _ambos(monkeypatch, fn):
    """Corre fn() con sheets y con postgres; devuelve (sheets, postgres)."""
    _modo(monkeypatch, "sheets")
    a = fn()
    _modo(monkeypatch, "postgres")
    b = fn()
    return a, b


def test_default_es_sheets(monkeypatch):
    monkeypatch.delenv("DATA_BACKEND", raising=False)
    monkeypatch.setattr(backend, "_from_dotenv", lambda k: None)
    assert backend.use_postgres() is False
    monkeypatch.setenv("DATA_BACKEND", "Postgres")
    assert backend.use_postgres() is True
    monkeypatch.setenv("DATA_BACKEND", "sheets")
    assert backend.use_postgres() is False


def test_mirror_default_false(monkeypatch):
    monkeypatch.delenv("MIRROR_WRITES_TO_SHEETS", raising=False)
    monkeypatch.setattr(backend, "_from_dotenv", lambda k: None)
    assert backend.mirror_writes() is False
    monkeypatch.setenv("MIRROR_WRITES_TO_SHEETS", "true")
    assert backend.mirror_writes() is True


def test_fuente_para():
    assert backend.fuente_para(MEDICA, None) == "medica"
    assert backend.fuente_para(MEDICA, "Otra") is None
    assert backend.fuente_para(NUTRI, TAB_NUTRI) == "nutricion"
    assert backend.fuente_para(NUTRI, "Otra") is None
    assert backend.fuente_para(FISICA, "Base Test") == "fisica_base_test"
    assert backend.fuente_para(FISICA, "base test") == "fisica_base_test"
    assert backend.fuente_para(S.sheet_id("central"), None) is None
    assert backend.fuente_para("desconocido", "x") is None


# --------------------------------------------------------------------------- paridad
@needs_live
def test_paridad_medica_dict_y_df(monkeypatch):
    from src.modules.areamedica import create_dataframe_from_sheet, read_google_sheet_with_headers
    a, b = _ambos(monkeypatch, lambda: read_google_sheet_with_headers(sheet_id=MEDICA))
    assert a["success"] == b["success"]
    assert a["columns"] == b["columns"]
    assert a["data"] == b["data"]
    assert a["raw_data"] == b["raw_data"]
    assert a["total_rows"] == b["total_rows"]
    a, b = _ambos(monkeypatch, create_dataframe_from_sheet)
    a = pd.DataFrame() if a is None else a
    b = pd.DataFrame() if b is None else b
    assert diff_frames(a, b) == []


@needs_live
def test_paridad_nutricion(monkeypatch):
    from src.modules.areanutricion import read_google_sheet_as_df
    a, b = _ambos(monkeypatch, lambda: read_google_sheet_as_df(NUTRI, TAB_NUTRI))
    assert diff_frames(a, b) == []


@needs_live
def test_paridad_fisica_cargar_hoja(monkeypatch):
    from src.modules.areafisica import cargar_hoja
    a, b = _ambos(monkeypatch, lambda: cargar_hoja(FISICA, "Base Test"))
    assert not a.empty
    assert diff_frames(a, b) == []


@needs_live
def test_paridad_pesos_por_dni(monkeypatch):
    from src.modules.areafisica import obtener_pesos_por_dni
    a, b = _ambos(monkeypatch, obtener_pesos_por_dni)
    assert diff_frames(a, b) == []


@needs_live
def test_paridad_dashboard_loaders(monkeypatch):
    from src.modules import dashboard_360 as d
    for nombre in ("obtener_df_medica", "obtener_df_nutricion", "obtener_df_fisica"):
        a, b = _ambos(monkeypatch, getattr(d, nombre))
        assert diff_frames(a, b) == [], nombre


@needs_live
def test_paridad_partidos(monkeypatch):
    from src.modules import panel_partido as p
    a, b = _ambos(monkeypatch, p._get_all_matches)
    assert a == b and a
    # 2 partidos (acota la cuota de la API): el dict parseado debe ser identico
    for nombre in a[:2]:
        sa, sb = _ambos(monkeypatch, lambda n=nombre: p._load_match_data(n))
        assert sa == sb


@needs_live
def test_paridad_reportemedico_conectar_area_medica(monkeypatch):
    from src.modules.reportemedico import conectar_area_medica
    a, b = _ambos(monkeypatch, conectar_area_medica)
    assert a == b


@needs_live
def test_bot_contexto_sin_error(monkeypatch):
    """El contexto del bot se arma con ambos backends; las secciones medica/fisica coinciden
    en estructura (el texto puede variar solo por formato de numeros)."""
    from src.modules.bot import load_all_data
    a, b = _ambos(monkeypatch, load_all_data)
    assert isinstance(a, str) and isinstance(b, str)
    if a.startswith("Error cargando datos") and "APIError" in a:
        pytest.skip("Google devolvio un error transitorio del lado Sheets")
    assert not b.startswith("Error cargando datos")
    assert ("FÍSICA" in a) == ("FÍSICA" in b)
    # la hoja usa 'Marca temporal' y no 'Fecha': la seccion fisica debe traer datos
    assert "FÍSICA: Error" not in b


# --------------------------------------------------------------------------- fallback
@needs_live
def test_fallback_con_db_caida(monkeypatch):
    import streamlit as st
    from src.data import db
    from src.modules.areanutricion import read_google_sheet_as_df

    _modo(monkeypatch, "sheets")
    esperado = read_google_sheet_as_df(NUTRI, TAB_NUTRI)

    db.dispose_engine()
    monkeypatch.setenv("DATABASE_URL", "postgresql://nadie:nada@127.0.0.1:1/nodb")
    monkeypatch.setattr(db.time, "sleep", lambda s: None)
    _modo(monkeypatch, "postgres")
    try:
        t0 = time.time()
        obtenido = read_google_sheet_as_df(NUTRI, TAB_NUTRI)  # cae a Sheets, no rompe
        assert diff_frames(esperado, obtenido) == []
        assert backend._caida_hasta > t0  # circuito abierto
        # 2da llamada: no reintenta la DB
        assert backend.leer(backend.df_nutricion) is backend.FALLBACK
        # el resto de los loaders tambien siguen funcionando
        from src.modules.areafisica import cargar_hoja
        assert not cargar_hoja(FISICA, "Base Test").empty
    finally:
        db.dispose_engine()
        st.cache_data.clear()
        backend.reset_caida()


def test_fallback_en_escritura_no_rompe(monkeypatch):
    """registrar_reporte devuelve False (sin excepcion) si la DB esta caida."""
    from src.data import db
    db.dispose_engine()
    monkeypatch.setenv("DATABASE_URL", "postgresql://nadie:nada@127.0.0.1:1/nodb")
    monkeypatch.setattr(db.time, "sleep", lambda s: None)
    try:
        assert backend.registrar_reporte("nutricion", ["x"]) is False
    finally:
        db.dispose_engine()


# --------------------------------------------------------------------------- escritura (schema temporal)
@pytest.fixture
def schema_conn():
    from src.data.db import connect
    from src.data.migrate import apply_migrations

    name = "test_" + uuid.uuid4().hex[:10]
    with connect() as conn:
        apply_migrations(conn, schema=name)
        yield name, conn
        conn.rollback()
        conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{name}" CASCADE')
        conn.commit()


def _prep(conn, schema, source, headers, synced_rows=()):
    import json
    conn.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
    conn.execute(text("INSERT INTO sheet_headers (source, headers) VALUES (:s, CAST(:h AS jsonb))"),
                 {"s": source, "h": json.dumps(headers)})
    for n, row in synced_rows:
        conn.execute(
            text("INSERT INTO sheet_rows (source,row_num,row_hash,data) "
                 "VALUES (:s,:n,'h',CAST(:d AS jsonb))"),
            {"s": source, "n": n, "d": json.dumps(dict(zip(headers, row)))})


@needs_db
def test_insertar_fila_nutricion(schema_conn):
    from src.data.writer import insertar_fila, insertar_fila_posicional
    schema, conn = schema_conn
    headers = ["Marca temporal", "Nombre y Apellido", "Dni", "Peso (kg)"]
    _prep(conn, schema, "nutricion", headers, [(1, ["01/01/2026 10:00", "A", "111", "70"])])

    n1 = insertar_fila("nutricion", {"Nombre y Apellido": "Test X", "Dni": "12.345.678",
                                     "Marca temporal": "15/03/2026 09:30", "Peso (kg)": 80.5},
                       conn=conn)
    assert n1 == APP_ROW_BASE
    n2 = insertar_fila_posicional("nutricion", ["16/03/2026 08:00", "Test Y", "99", 71], conn=conn)
    assert n2 == APP_ROW_BASE + 1

    rows = conn.execute(text(
        "SELECT row_num, dni, fecha::text, data FROM sheet_rows WHERE source='nutricion' "
        "AND row_num >= :b ORDER BY row_num"), {"b": APP_ROW_BASE}).all()
    assert rows[0].dni == "12345678" and rows[0].fecha == "2026-03-15"
    assert rows[0].data == {"Marca temporal": "15/03/2026 09:30", "Nombre y Apellido": "Test X",
                            "Dni": "12.345.678", "Peso (kg)": "80.5"}
    assert rows[1].data["Peso (kg)"] == "71" and rows[1].dni == "99"

    with pytest.raises(ValueError):
        insertar_fila("nutricion", {"No existe": "x"}, conn=conn)
    with pytest.raises(ValueError):
        insertar_fila("fisica_base_test", {"a": "b"}, conn=conn)


@needs_db
def test_insertar_fila_medica_headers_genericos(schema_conn):
    """Hoja medica real: headers 'Columna N'; DNI y fecha salen de la posicion del reporte."""
    from src.data.writer import insertar_fila_posicional
    schema, conn = schema_conn
    _prep(conn, schema, "medica", [f"Columna {i}" for i in range(1, 19)])
    n = insertar_fila_posicional(
        "medica", ["15/03/2026 10:00", "Dr", "2026-03-15", "Test Z", "30111222", "M"], conn=conn)
    assert n == APP_ROW_BASE
    r = conn.execute(text("SELECT dni, fecha::text, data FROM sheet_rows WHERE source='medica'")).one()
    assert r.dni == "30111222" and r.fecha == "2026-03-15"
    assert r.data["Columna 4"] == "Test Z" and r.data["Columna 18"] == ""


@needs_db
def test_insertar_sin_headers_falla(schema_conn):
    from src.data.writer import insertar_fila_posicional
    schema, conn = schema_conn
    conn.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
    with pytest.raises(RuntimeError):
        insertar_fila_posicional("nutricion", ["x"], conn=conn)


@needs_db
def test_sync_limpia_filas_espejadas(schema_conn):
    """Con MIRROR_WRITES_TO_SHEETS la fila queda en Sheets y en la DB: el sync borra la
    copia local cuando ya trajo la fila del Sheet (sin duplicados). Las no espejadas quedan."""
    from src.data.sync import _apply_source
    from src.data.writer import insertar_fila_posicional
    schema, conn = schema_conn
    headers = ["Marca temporal", "Nombre y Apellido", "Dni"]
    _prep(conn, schema, "nutricion", headers)
    insertar_fila_posicional("nutricion", ["a", "viejo espejado", "1"], mirrored_at=100.0, conn=conn)
    insertar_fila_posicional("nutricion", ["b", "espejado reciente", "2"], mirrored_at=500.0, conn=conn)
    insertar_fila_posicional("nutricion", ["c", "solo db", "3"], conn=conn)
    _apply_source(conn, "nutricion", headers, [], False, fetched_at=300.0)
    nombres = [r[0] for r in conn.execute(text(
        "SELECT data->>'Nombre y Apellido' FROM sheet_rows WHERE source='nutricion' "
        "ORDER BY row_num"))]
    assert nombres == ["espejado reciente", "solo db"]


@needs_db
def test_insertar_fila_publica_con_conexion_propia(schema_conn, monkeypatch):
    """Sin `conn`: abre su transaccion, confirma y no deja estado de sesion."""
    from src.data import writer
    schema, conn = schema_conn
    headers = ["Marca temporal", "Dni"]
    _prep(conn, schema, "nutricion", headers)
    conn.commit()  # headers visibles para otra conexion

    from src.data import db
    real_connect = db.connect

    class _Conn:
        def __init__(self):
            self.c = real_connect()
            self.c.exec_driver_sql(f'SET search_path TO "{schema}"')

        def __enter__(self):
            return self.c

        def __exit__(self, *a):
            self.c.exec_driver_sql("RESET search_path")
            self.c.commit()
            self.c.close()

    monkeypatch.setattr(writer, "connect", lambda: _Conn())
    n = writer.insertar_fila("nutricion", {"Dni": "555"})
    assert n == APP_ROW_BASE
    conn.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
    assert conn.execute(text("SELECT count(*) FROM sheet_rows WHERE source='nutricion'")).scalar() == 1
