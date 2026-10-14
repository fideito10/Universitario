"""Selector de backend de datos (Sheets | PostgreSQL) para las pantallas.

DATA_BACKEND=sheets (default) | postgres. Se lee de la variable de entorno, del
archivo .env de la raiz o de st.secrets (en ese orden).

Con `postgres`, los loaders de medica, nutricion, fisica_base_test y partidos
llaman a los wrappers de este modulo (cache `st.cache_data` 5 min sobre `repo.*`).
Si la DB falla, `leer()` devuelve FALLBACK y el loader usa Sheets como hoy; el
aviso se muestra una sola vez por sesion y la DB no se reintenta durante
`_REINTENTO_SEG` segundos (evita colgar cada click con una DB caida).

Las tablas propias de la app (Usuarios, Jugadores_Maestro, Wellness_Jugador,
Asistencias) viven en `src/data/repo_app.py` (Fase 4): con `postgres` se leen y escriben
ahi, SIN fallback a Sheets (la DB es la fuente de verdad); los modulos solo consultan
`use_postgres()` / `mirror_writes()` y llaman a `limpiar_cache()` tras escribir.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import streamlit as st

from src.data import repo, sources as S
from src.data.rows import APP_ROW_BASE  # noqa: F401  (re-export)
from src.data.writer import insertar_fila, insertar_fila_posicional  # noqa: F401
from src.utils.cache import cache_si_ok

_ROOT = Path(__file__).resolve().parents[2]
_REINTENTO_SEG = 60
_caida_hasta = 0.0  # epoch hasta el cual no se reintenta Postgres tras un fallo

FALLBACK = object()  # sentinela: "usar el loader de Sheets"

_TRUE = ("1", "true", "yes", "si", "on")


# --------------------------------------------------------------------------- config
def _from_dotenv(key: str) -> str | None:
    try:
        for line in (_ROOT / ".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip().removeprefix("export ").strip() == key:
                return v.strip().strip('"').strip("'") or None
    except OSError:
        pass
    return None


def _setting(key: str, default: str = "") -> str:
    val = os.environ.get(key) or _from_dotenv(key)
    if not val:
        try:
            val = st.secrets.get(key)
        except Exception:
            val = None
    return str(val).strip() if val else default


def use_postgres() -> bool:
    return _setting("DATA_BACKEND", "sheets").lower() == "postgres"


def mirror_writes() -> bool:
    """MIRROR_WRITES_TO_SHEETS (default false): ademas de la DB, agrega la fila al Sheet."""
    return _setting("MIRROR_WRITES_TO_SHEETS", "false").lower() in _TRUE


# --------------------------------------------------------------------------- fallback
def _avisar_una_vez(exc: Exception) -> None:
    try:
        if st.session_state.get("_pg_fallback_avisado"):
            return
        st.session_state["_pg_fallback_avisado"] = True
        st.warning("⚠️ Base de datos no disponible: se muestran datos directos de Google Sheets "
                   "(puede tardar más).")
    except Exception:
        pass


def reset_caida() -> None:
    global _caida_hasta
    _caida_hasta = 0.0


def leer(fn, *args):
    """Ejecuta un wrapper de lectura. Devuelve FALLBACK (y avisa 1 vez) si Postgres falla."""
    global _caida_hasta
    if time.time() < _caida_hasta:
        return FALLBACK
    try:
        return fn(*args)
    except Exception as exc:
        _caida_hasta = time.time() + _REINTENTO_SEG
        _avisar_una_vez(exc)
        return FALLBACK


# --------------------------------------------------------------------------- lecturas (cache 5 min)
def _siempre(_r) -> bool:
    return True  # un DataFrame vacio es un resultado valido (p.ej. hoja medica sin filas)


@cache_si_ok(ttl=300, ok=_siempre)
def df_medica():
    return repo.df_medica()


@cache_si_ok(ttl=300, ok=_siempre)
def df_nutricion():
    return repo.df_nutricion()


@cache_si_ok(ttl=300, ok=_siempre)
def df_fisica():
    return repo.df_fisica_base_test()


@cache_si_ok(ttl=300, ok=_siempre)
def values_medica() -> list:
    """get_all_values() de la hoja medica ([] si esta vacia)."""
    return repo._all_values("medica")


@cache_si_ok(ttl=300, ok=_siempre)
def lista_partidos() -> list:
    return repo.lista_partidos()


@cache_si_ok(ttl=300, ok=_siempre)
def rows_partido(nombre: str) -> list:
    return repo.rows_partido(nombre)


def limpiar_cache() -> None:
    for fn in (df_medica, df_nutricion, df_fisica, values_medica, lista_partidos,
               rows_partido, minutos_desde_sync):
        try:
            fn.clear()
        except Exception:
            pass
    try:
        st.cache_data.clear()
    except Exception:
        pass


# --------------------------------------------------------------------------- mapeo Sheet -> fuente
def _norm_tab(name) -> str:
    return str(name or "").strip().lower().replace(" ", "")


def fuente_para(sheet_id: str | None, worksheet_name: str | None = None) -> str | None:
    """Fuente de Postgres que espeja ese (sheet, pestana), o None si no esta en sources."""
    if not sheet_id:
        return None
    if sheet_id == S.sheet_id("medica"):
        return "medica" if not worksheet_name else None
    if sheet_id == S.sheet_id("nutricion"):
        return "nutricion" if _norm_tab(worksheet_name) == _norm_tab(S.tab_name("nutricion")) else None
    if sheet_id == S.sheet_id("fisica"):
        return "fisica_base_test" if _norm_tab(worksheet_name) == _norm_tab(S.tab_name("fisica")) else None
    return None


def df_de_fuente(fuente: str):
    """DataFrame de la fuente via Postgres, o FALLBACK si hay que usar Sheets."""
    fn = {"medica": df_medica, "nutricion": df_nutricion, "fisica_base_test": df_fisica}[fuente]
    return leer(fn)


# --------------------------------------------------------------------------- escrituras
def registrar_reporte(source: str, valores: list, mirrored_at: float | None = None) -> bool:
    """Inserta un reporte (lista posicional) en sheet_rows y limpia el cache.

    True si quedo en la DB; False si fallo (el llamador decide el fallback a Sheets).
    """
    try:
        insertar_fila_posicional(source, valores, mirrored_at=mirrored_at)
    except Exception as exc:
        _avisar_una_vez(exc)
        return False
    limpiar_cache()
    return True


# --------------------------------------------------------------------------- frescura / sync
@cache_si_ok(ttl=60, ok=_siempre)
def minutos_desde_sync():
    """Minutos desde la ultima sync OK (la fuente mas atrasada), o None si no hay datos."""
    from sqlalchemy import text

    from src.data.db import connect
    from src.data.sync import ALL_SOURCES

    with connect() as conn:
        seg = conn.execute(text(
            "SELECT EXTRACT(EPOCH FROM (now() - min(t))) FROM ("
            "SELECT max(finished_at) AS t FROM sync_runs "
            "WHERE status = 'ok' AND source = ANY(:s) GROUP BY source) x"),
            {"s": list(ALL_SOURCES)}).scalar()
    return None if seg is None else int(seg // 60)


def mostrar_frescura() -> None:
    """'Datos actualizados hace X min' (solo con backend postgres; nunca rompe la pantalla)."""
    if not use_postgres():
        return
    try:
        if time.time() < _caida_hasta:
            return
        mins = minutos_desde_sync()
    except Exception:
        return
    if mins is None:
        return
    txt = "hace menos de 1 min" if mins < 1 else f"hace {mins} min" if mins < 120 \
        else f"hace {mins // 60} h"
    st.caption(f"🕒 Datos actualizados {txt}")


def sincronizar_ahora() -> list[dict]:
    from src.data.sync import run_sync

    res = run_sync()
    limpiar_cache()
    return res


def boton_sincronizar(rol: str | None, key: str = "btn_sync_ahora") -> None:
    """Boton 'Sincronizar ahora': solo rol Administrador y backend postgres."""
    if not use_postgres() or str(rol or "").strip() != "Administrador":
        return
    if st.button("🔄 Sincronizar ahora", use_container_width=True, key=key):
        with st.spinner("Sincronizando con Google Sheets..."):
            try:
                res = sincronizar_ahora()
            except Exception as exc:
                st.error(f"❌ No se pudo sincronizar: {type(exc).__name__}")
                return
        if any(r.get("status") == "error" for r in res):
            st.warning("⚠️ La sincronización terminó con errores en alguna fuente.")
        else:
            st.success("✅ Datos sincronizados")
