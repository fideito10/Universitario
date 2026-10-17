"""Sesion recordada ("Recordarme"): token firmado en una cookie del navegador.

El token NO contiene la clave: solo usuario y vencimiento, firmados con HMAC-SHA256 y el secreto
SESSION_SECRET (variable de entorno o st.secrets). Sin secreto la funcion queda apagada.
Al restaurar, el usuario se vuelve a buscar en la tabla (ver AuthManager.restore_session), asi un
usuario borrado o un cambio de rol se respetan aunque el token siga vigente.
"""
import base64
import hashlib
import hmac
import json
import os
import time

COOKIE_NAME = "uni_session"
DIAS_VIGENCIA = 30


def _secret() -> bytes | None:
    s = os.environ.get("SESSION_SECRET")
    if not s:
        try:
            import streamlit as st
            s = st.secrets.get("SESSION_SECRET")
        except Exception:
            s = None
    return str(s).encode() if s and len(str(s)) >= 16 else None


def habilitado() -> bool:
    return _secret() is not None


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _firma(payload: str, secret: bytes) -> str:
    return _b64(hmac.new(secret, payload.encode(), hashlib.sha256).digest())


def crear_token(username: str, ahora: float | None = None) -> str | None:
    secret = _secret()
    if not secret or not str(username).strip():
        return None
    exp = int((ahora if ahora is not None else time.time()) + DIAS_VIGENCIA * 86400)
    payload = _b64(json.dumps({"u": str(username).strip(), "exp": exp}, separators=(",", ":")).encode())
    return f"{payload}.{_firma(payload, secret)}"


def validar_token(token: str | None, ahora: float | None = None) -> str | None:
    """Devuelve el usuario si el token es autentico y no vencio; si no, None."""
    secret = _secret()
    if not secret or not token or token.count(".") != 1:
        return None
    payload, firma = token.split(".")
    if not hmac.compare_digest(firma, _firma(payload, secret)):
        return None
    try:
        data = json.loads(_unb64(payload))
        if data["exp"] < (ahora if ahora is not None else time.time()):
            return None
        return str(data["u"]) or None
    except Exception:
        return None


def token_de_cookies() -> str | None:
    """Lee la cookie del request actual (st.context.cookies, Streamlit >= 1.37)."""
    try:
        import streamlit as st
        return st.context.cookies.get(COOKIE_NAME)
    except Exception:
        return None


def js_guardar_cookie(token: str) -> str:
    max_age = DIAS_VIGENCIA * 86400
    return (f"<script>try{{window.parent.document.cookie="
            f"'{COOKIE_NAME}={token}; Max-Age={max_age}; path=/; SameSite=Lax; Secure';}}catch(e){{}}</script>")


def js_borrar_cookie() -> str:
    return (f"<script>try{{window.parent.document.cookie="
            f"'{COOKIE_NAME}=; Max-Age=0; path=/; SameSite=Lax; Secure';}}catch(e){{}}</script>")
