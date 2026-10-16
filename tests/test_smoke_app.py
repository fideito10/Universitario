"""Smoke de pantallas con streamlit.testing.v1.AppTest, con ambos backends.

Simula una sesion autenticada (Administrador) y ejecuta cada pantalla; falla si hay
excepcion no controlada. No hace clics de escritura. Con DATA_BACKEND=sheets lee Google
en vivo (solo lectura); con postgres lee la DB.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_parity import _have_db, _have_google  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (_have_google() and _have_db()),
    reason="requiere credenciales de Google y DATABASE_URL",
)

USER = {"usuario": "admin", "rol": "Administrador", "nombre": "Admin Sistema", "dni": ""}

SCREENS = {
    "dashboard_360": "from src.modules.dashboard_360 import panel_profesional_jugador as f; f()",
    "nutricion": "from src.modules.areanutricion import main_nutricion as f; f()",
    "fisica": "from src.modules.areafisica import physical_area as f; f()",
    "medica": "from src.modules.areamedica import main_streamlit as f; f()",
    "reporte_medico": "from src.modules.reportemedico import main_reporte_medico as f; f()",
    "analisis_partido": "from src.modules.panel_partido import rugby_analysis_module as f; f()",
    "bot": "from src.modules.bot import main_bot as f; f()",
}


def _run(code: str, monkeypatch, backend_name: str):
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    from src.data import backend

    monkeypatch.setenv("DATA_BACKEND", backend_name)
    backend.reset_caida()
    st.cache_data.clear()
    at = AppTest.from_string(f"import sys; sys.path.insert(0, r'{ROOT}')\n{code}\n",
                             default_timeout=180)
    at.session_state["authenticated"] = True
    at.session_state["user"] = dict(USER)
    return at.run()


@pytest.mark.parametrize("backend_name", ["sheets", "postgres"])
@pytest.mark.parametrize("screen", sorted(SCREENS))
def test_pantalla_sin_excepciones(screen, backend_name, monkeypatch):
    at = _run(SCREENS[screen], monkeypatch, backend_name)
    assert not at.exception, [e.value for e in at.exception]


@pytest.mark.parametrize("backend_name", ["sheets", "postgres"])
def test_main_importa_y_dashboard_inicio(backend_name, monkeypatch):
    """main() autenticado: renderiza el Home (con 'Datos actualizados' si postgres)."""
    at = _run("import main_universitario as m; m.main()", monkeypatch, backend_name)
    assert not at.exception, [e.value for e in at.exception]
    textos = " ".join(str(c.value) for c in at.caption)
    assert ("Datos actualizados" in textos) == (backend_name == "postgres")
    botones = [b.label for b in at.sidebar.button]
    assert any("Sincronizar ahora" in b for b in botones) == (backend_name == "postgres")
