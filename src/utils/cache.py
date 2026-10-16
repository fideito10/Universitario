"""
Cache de lecturas (st.cache_data) que no guarda resultados fallidos.
"""

import functools
import streamlit as st


class _NoCachear(Exception):
    def __init__(self, resultado):
        super().__init__("resultado no cacheable")
        self.resultado = resultado


def _ok_por_defecto(r):
    if r is None:
        return False
    if isinstance(r, dict) and "success" in r:
        return bool(r.get("success"))
    if hasattr(r, "empty"):
        return not r.empty
    return True


def cache_si_ok(ttl=300, ok=None):
    """
    Cachea el resultado solo si `ok(resultado)` es True (por defecto: dict con
    success=True, DataFrame no vacío, o cualquier valor no None). Si no, devuelve
    el resultado igual pero sin dejarlo cacheado. Expone `.clear()`.
    """
    chequear = ok or _ok_por_defecto

    def deco(fn):
        def _cacheada(*args, **kwargs):
            r = fn(*args, **kwargs)
            if not chequear(r):
                raise _NoCachear(r)
            return r

        # st.cache_data identifica la funcion por modulo + qualname + codigo fuente. Como
        # todas las `_cacheada` son identicas, sin esto compartirian clave de cache (dos
        # loaders sin argumentos devolverian el resultado del otro y los anidados se
        # bloquearian entre si). Se le da a cada una la identidad de la funcion real.
        _cacheada.__module__ = fn.__module__
        _cacheada.__qualname__ = f"{fn.__qualname__}[cache_si_ok]"
        _cacheada = st.cache_data(ttl=ttl, show_spinner=False)(_cacheada)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return _cacheada(*args, **kwargs)
            except _NoCachear as e:
                return e.resultado

        wrapper.clear = _cacheada.clear
        return wrapper

    return deco
