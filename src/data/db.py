"""Conexion a PostgreSQL (SQLAlchemy 2 + psycopg3).

La URL se resuelve en este orden: variable de entorno DATABASE_URL, archivo
.env en la raiz del repo, st.secrets["DATABASE_URL"]. Nunca se loguea.
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_lock = threading.Lock()
_engine = None


def _from_dotenv(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip().removeprefix("export ").strip() == "DATABASE_URL":
                return val.strip().strip('"').strip("'") or None
    except OSError:
        pass
    return None


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL") or _from_dotenv(_ROOT / ".env")
    if not url:
        try:
            import streamlit as st

            url = st.secrets.get("DATABASE_URL")
        except Exception:
            url = None
    if not url:
        raise RuntimeError(
            "DATABASE_URL no configurada (variable de entorno, .env o st.secrets)."
        )
    # SQLAlchemy necesita el driver explicito para usar psycopg3.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def _build_engine():
    from sqlalchemy import create_engine

    return create_engine(
        get_database_url(),
        pool_size=3,
        max_overflow=2,
        pool_pre_ping=True,
        pool_recycle=300,  # Neon suspende conexiones inactivas
        connect_args={"connect_timeout": 15},
    )


def _in_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx(suppress_warning=True) is not None
    except Exception:
        return False


def _streamlit_engine():
    import streamlit as st

    @st.cache_resource(show_spinner=False)
    def _cached():
        return _build_engine()

    return _cached()


def get_engine():
    """Engine compartido (st.cache_resource en Streamlit, singleton fuera)."""
    global _engine
    if _in_streamlit():
        return _streamlit_engine()
    with _lock:
        if _engine is None:
            _engine = _build_engine()
        return _engine


def dispose_engine() -> None:
    global _engine
    with _lock:
        if _engine is not None:
            _engine.dispose()
            _engine = None


def connect(retries: int = 4, delay: float = 2.0):
    """Abre una conexion con reintento corto (arranque en frio de Neon).

    Uso: ``with connect() as conn: conn.execute(text(...))``
    """
    from sqlalchemy.exc import OperationalError

    engine = get_engine()
    last = None
    for attempt in range(retries):
        try:
            return engine.connect()
        except OperationalError as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
    raise last
