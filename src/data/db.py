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
        pool_size=10,        # sesiones concurrentes + hilo de precalentamiento
        max_overflow=5,
        pool_timeout=30,
        pool_use_lifo=True,  # reutiliza las conexiones mas recientes (las demas caducan solas)
        pool_pre_ping=True,  # Neon suspende el compute a ~5 min: detecta la conexion muerta y reabre
        pool_recycle=900,
        connect_args={"connect_timeout": 15},
    )


def get_engine():
    """Engine compartido por todo el proceso (singleton de modulo).

    No usa st.cache_resource a proposito: asi el hilo de precalentamiento (sin
    contexto de Streamlit) y las sesiones comparten el MISMO pool.
    """
    global _engine
    if _engine is not None:
        return _engine
    with _lock:
        if _engine is None:
            _engine = _build_engine()
        return _engine


def warm_pool(n: int = 3) -> None:
    """Abre ``n`` conexiones a la vez y las devuelve al pool (despierta Neon y evita el
    costo de conexion/TLS en las primeras consultas)."""
    from sqlalchemy import text

    conns = []
    try:
        for _ in range(max(1, n)):
            c = connect()
            c.execute(text("SELECT 1"))
            conns.append(c)
    finally:
        for c in conns:
            try:
                c.close()
            except Exception:
                pass


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
