"""Check-in por QR: vinculacion de celus y registro de Presente (schema temporal)."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_app_tables import _seed, needs_db, pg  # noqa: E402,F401


def _heads(run):
    run("INSERT INTO sheet_headers (source, headers) VALUES ('app:asistencias', CAST(:h AS jsonb))",
        h=json.dumps(["Fecha", "Categoria", "Tipo_Actividad", "DNI", "Nombre", "Apellido",
                      "Estado_Asistencia", "Observaciones"]))


@needs_db
def test_verificar_jugador(pg):
    from src.data import repo_checkin as rc
    _seed(pg, jugadores=[("12345678", "Juan", "Perez", "M19", "Activo"),
                         ("22222222", "Ana", "Gomez", "M19", "Inactivo")])
    assert rc.verificar_jugador("12.345.678", "01/01/2000")["nombre"] == "Juan"
    assert rc.verificar_jugador("12345678", "02/01/2000") is None   # nacimiento distinto
    assert rc.verificar_jugador("99999999", "01/01/2000") is None   # DNI inexistente
    assert rc.verificar_jugador("22222222", "01/01/2000") is None   # inactivo
    assert rc.verificar_jugador("12345678", "") is None


@needs_db
def test_dispositivos_limite_y_reset(pg):
    from src.data import repo_checkin as rc
    t1 = rc.vincular_dispositivo("12345678", "celu 1")
    t2 = rc.vincular_dispositivo("12345678", "celu 2")
    assert rc.dni_de_token(t1) == "12345678" and rc.dni_de_token(t2) == "12345678"
    assert rc.dni_de_token("token-falso") is None
    with pytest.raises(rc.LimiteDispositivos):
        rc.vincular_dispositivo("12345678", "celu 3")
    assert rc.revocar_dispositivos("12345678") == 2
    assert rc.dni_de_token(t1) is None
    rc.vincular_dispositivo("12345678", "celu nuevo")  # ya hay lugar


@needs_db
def test_presente_nuevo_repetido_y_correccion(pg):
    from src.data import repo_checkin as rc
    _heads(pg)
    _seed(pg, jugadores=[("12345678", "Juan", "Perez", "M19", "Activo")])
    r, jug = rc.registrar_presente("12345678")
    assert r == "nuevo" and jug["categoria"] == "M19"
    assert rc.registrar_presente("12345678")[0] == "repetido"
    assert [p["DNI"] for p in rc.presentes_hoy()] == ["12345678"]
    n = pg("SELECT count(*) FROM asistencias")[0][0]
    assert n == 1                                          # sin duplicados
    assert rc.registrar_presente("00000000")[0] == "inexistente"

    # El entrenador lo cargo como Ausente antes: el QR lo corrige en la misma fila.
    pg("UPDATE asistencias SET estado='Ausente', "
       "extra = jsonb_set(extra, '{Estado_Asistencia}', '\"Ausente\"')")
    assert rc.registrar_presente("12345678")[0] == "nuevo"
    assert pg("SELECT count(*), min(estado) FROM asistencias")[0] == (1, "Presente")
