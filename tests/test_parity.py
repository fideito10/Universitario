"""Paridad Google Sheets (en vivo) vs PostgreSQL (repo.*).

Corre solo si hay credenciales de Google Y DATABASE_URL, y la DB ya esta sincronizada
(py -m src.data.sync; py scripts/import_app_tables.py). Las diferencias se reportan
solo con indices/columnas, nunca con valores.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import sources as S  # noqa: E402


def _have_google():
    try:
        from src.utils.credentials import get_credentials_dict
        return get_credentials_dict() is not None
    except Exception:
        return False


def _have_db():
    try:
        from src.data.db import connect
        from sqlalchemy import text
        with connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not (_have_google() and _have_db()),
    reason="requiere credenciales de Google y DATABASE_URL",
)


@pytest.fixture(scope="module")
def gc():
    from src.utils.credentials import get_gspread_client
    return get_gspread_client()


def _retry(fn, *a, **k):
    from src.data.sync import _with_backoff
    return _with_backoff(fn, *a, **k)


def _ws(gc, key, tab=None):
    sh = _retry(gc.open_by_key, S.sheet_id(key))
    if tab is None:
        return _retry(sh.get_worksheet, 0)
    return _retry(sh.worksheet, tab)


def diff_frames(live: pd.DataFrame, db: pd.DataFrame) -> list[str]:
    out = []
    lc, dc = [str(c) for c in live.columns], [str(c) for c in db.columns]
    if lc != dc:
        out.append(f"columnas distintas: live={len(lc)} db={len(dc)} "
                   f"solo_live={[c for c in lc if c not in dc]} "
                   f"solo_db={[c for c in dc if c not in lc]} orden_igual_set={sorted(lc) == sorted(dc)}")
        return out
    if len(live) != len(db):
        out.append(f"filas distintas: live={len(live)} db={len(db)}")
        return out
    a = live.astype(str).reset_index(drop=True).values
    b = db.astype(str).reset_index(drop=True).values
    bad = (a != b)
    if bad.any():
        coords = list(zip(*bad.nonzero()))
        out.append(f"{len(coords)} celdas distintas; ejemplos (fila, columna): "
                   f"{[(int(r), lc[c]) for r, c in coords[:5]]}")
    return out


def diff_rows(live: list[list[str]], db: list[list[str]]) -> list[str]:
    out = []
    if len(live) != len(db):
        out.append(f"filas distintas: live={len(live)} db={len(db)}")
    n = min(len(live), len(db))
    bad = [i for i in range(n) if live[i] != db[i]]
    if bad:
        out.append(f"{len(bad)} filas distintas; primeros indices: {bad[:5]}")
    return out


# ---------------------------------------------------------------- Sheets espejados
def test_medica(gc):
    from src.data import repo
    values = _retry(_ws(gc, "medica").get_all_values)
    live = pd.DataFrame([{c: (r[i] if i < len(r) else "") for i, c in enumerate(values[0])}
                         for r in values[1:]]) if values else pd.DataFrame()
    assert diff_frames(live, repo.df_medica()) == []
    # y los valores crudos (headers incluidos)
    from src.data.repo import _all_values
    assert diff_rows(values, _all_values("medica")) == []


def test_nutricion(gc):
    from src.data import repo
    data = _retry(_ws(gc, "nutricion", S.tab_name("nutricion")).get_all_values)
    live = pd.DataFrame(data[1:], columns=data[0])
    live = live.loc[:, ~live.columns.astype(str).str.contains("^Unnamed")]
    assert diff_frames(live, repo.df_nutricion()) == []
    from src.data.repo import _all_values
    assert diff_rows(data, _all_values("nutricion")) == []


def test_fisica_base_test(gc):
    from src.data import repo
    data = _retry(_ws(gc, "fisica", S.tab_name("fisica")).get_all_values)
    from src.data.repo import _all_values
    assert diff_rows(data, _all_values("fisica_base_test")) == []
    assert not repo.df_fisica_base_test().empty


def test_partidos(gc):
    from src.data import repo
    sh = _retry(gc.open_by_key, S.sheet_id("partidos"))
    wss = _retry(sh.worksheets)
    assert [w.title for w in wss] == repo.lista_partidos()
    problems = {}
    for w in wss:
        d = diff_rows(_retry(w.get_all_values), repo.rows_partido(w.title))
        if d:
            problems[w.title] = d
    assert problems == {}


# ---------------------------------------------------------------- Tablas de la app
@pytest.mark.parametrize("key,fn", [
    ("jugadores", "df_jugadores"), ("usuarios", "df_usuarios"), ("wellness", "df_wellness"),
])
def test_app_tables(gc, key, fn):
    from src.data import repo
    live = pd.DataFrame(_retry(_ws(gc, "central", S.tab_name(key)).get_all_records))
    db = getattr(repo, fn)()
    assert diff_frames(live, db) == []
    # tipos: get_all_records devuelve int/float; deben coincidir celda a celda
    for c in live.columns:
        assert [type(x) for x in live[c]] == [type(x) for x in db[c]], f"tipos distintos en {c}"


# ---------------------------------------------------------------- Loaders reales (si importan)
def _original(modname, attr):
    try:
        mod = __import__(f"src.modules.{modname}", fromlist=[attr])
        fn = getattr(mod, attr)
        return getattr(fn, "__wrapped__", fn)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"no se pudo importar {modname}.{attr}: {type(exc).__name__}")


def test_loader_original_nutricion():
    from src.data import repo
    fn = _original("areanutricion", "read_google_sheet_as_df")
    live = fn(S.sheet_id("nutricion"), S.tab_name("nutricion"))
    assert live is not None
    assert diff_frames(live, repo.df_nutricion()) == []


def test_loader_original_fisica():
    from src.data import repo
    fn = _original("areafisica", "_leer_hoja")
    from src.utils.credentials import get_credentials_dict
    live = fn(S.sheet_id("fisica"), S.tab_name("fisica"), get_credentials_dict())
    assert diff_frames(live, repo.df_fisica_base_test()) == []


def test_loader_original_medica():
    from src.data import repo
    fn = _original("areamedica", "create_dataframe_from_sheet")
    live = fn(S.sheet_id("medica"), None)
    live = pd.DataFrame() if live is None else live
    assert diff_frames(live, repo.df_medica()) == []
