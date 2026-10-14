"""La carga en bloque de partidos devuelve exactamente lo mismo que la individual."""
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_parity import _have_db  # noqa: E402

needs_db = pytest.mark.skipif(not _have_db(), reason="sin DATABASE_URL")


@needs_db
def test_todos_los_partidos_igual_que_individual():
    from src.data import repo

    nombres = repo.lista_partidos()
    assert nombres
    t0 = time.perf_counter()
    bloque = repo.todos_los_partidos()
    t_bloque = time.perf_counter() - t0

    assert set(nombres) <= set(bloque), "faltan partidos en la carga en bloque"
    for n in nombres:
        assert bloque[n] == repo.rows_partido(n), f"difiere el partido {n!r}"
    # una sola consulta: no debe tardar como 23 viajes secuenciales
    assert t_bloque < 15


@needs_db
def test_backend_rows_partido_usa_el_bloque():
    from src.data import backend, repo

    backend.limpiar_cache()
    n = repo.lista_partidos()[0]
    a = backend.rows_partido(n)
    b = backend.rows_partido(n)
    assert a == repo.rows_partido(n)
    assert a is b  # segunda llamada: sin viaje ni copia
