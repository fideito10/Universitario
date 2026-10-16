"""IDs de Google Sheets y nombres de pestanas, centralizados.

Cada valor puede sobreescribirse con una variable de entorno:
  SHEET_ID_<CLAVE> y TAB_<CLAVE>  (p.ej. SHEET_ID_MEDICA, TAB_NUTRICION).
Sin dependencias de Streamlit.
"""
from __future__ import annotations

import os

_DEFAULT_IDS = {
    # "UnI Base de datos": Jugadores_Maestro, Usuarios, Wellness_Jugador (Asistencias se crea aca)
    "central": "1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw",
    # "Uni Reporte Medico": 1 pestana (Reportes)
    "medica": "1ham2WSMQa3eEv0V0TtHcAa55R3WLGoBje6pSOoNxcBQ",
    # "Uni Nutricion"
    "nutricion": "1CpAklgxgcVJrIWRWt-yJW4u6EkTcIeQqqp87kllsUqo",
    # "Uni Base Fisica "
    "fisica": "1sR4wWsA0_nZGS011d6QV84znTnRW4d7iS65y2oBjvYI",
    # "Datos Partidos ": una pestana por partido
    "partidos": "1JXKJkDYcrOHRQ4fmC1uPkEW4crLNdJhzJLcwbMdOICU",
    # Legado "CAR Rugby Club - Reporte Medico (respuestas)": solo lo usa por defecto
    # FormulariosGoogleSheets (src/sheets/formularios_google_sheets.py). No se sincroniza.
    "legacy_car": "1zGyW-M_VV7iyDKVB1TTd0EEP3QBjdoiBmSJN2tK-H7w",
}

# Pestana de cada fuente. None = primera pestana del spreadsheet.
_DEFAULT_TABS = {
    "medica": None,  # el codigo actual usa get_worksheet(0) (hoy "Reportes")
    "nutricion": "Respuestas de formulario 1",
    "fisica": "Base Test",
    "jugadores": "Jugadores_Maestro",
    "usuarios": "Usuarios",
    "wellness": "Wellness_Jugador",
    "asistencias": "Asistencias",
}


def sheet_id(key: str) -> str:
    return os.environ.get(f"SHEET_ID_{key.upper()}") or _DEFAULT_IDS[key]


def tab_name(key: str) -> str | None:
    return os.environ.get(f"TAB_{key.upper()}") or _DEFAULT_TABS[key]


# Fuentes espejadas por el sync: nombre logico -> (clave de sheet, clave de pestana)
SYNC_SOURCES = {
    "medica": ("medica", "medica"),
    "nutricion": ("nutricion", "nutricion"),
    "fisica_base_test": ("fisica", "fisica"),
}
PARTIDO_PREFIX = "partido:"
PARTIDOS_INDEX = "__partidos_index__"  # sheet_headers: orden de pestanas de partidos
