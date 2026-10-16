"""Precalentamiento al arrancar el proceso (solo DATA_BACKEND=postgres).

Un hilo daemon, lanzado una sola vez por proceso, abre el pool a Neon (despierta el
compute suspendido) y deja en cache los partidos, que son lo mas pesado. La pantalla
de login no espera: si el usuario llega antes, las consultas normales se hacen igual.
No toca Sheets ni escribe en la DB. Nunca propaga errores.
"""
from __future__ import annotations

import threading

_lock = threading.Lock()
_lanzado = False


def _tarea() -> None:
    try:
        from src.data import backend, db

        db.warm_pool(3)
        backend._todos_partidos()  # cache de modulo (TTL 5 min), sin st.cache_data
    except Exception:
        pass


def iniciar() -> bool:
    """Lanza el precalentamiento una vez por proceso. True si lo lanzo esta vez."""
    global _lanzado
    from src.data.backend import use_postgres

    if not use_postgres():
        return False
    with _lock:
        if _lanzado:
            return False
        _lanzado = True
    threading.Thread(target=_tarea, name="warmup-db", daemon=True).start()
    return True
