"""Entrar con Google (OIDC nativo de Streamlit: st.login / st.user).

Solo deja pasar mails que ya estan en la tabla de usuarios (o de jugadores con DATA_BACKEND=postgres);
ver AuthManager.login_by_email. Se activa con GOOGLE_OAUTH_CLIENT_ID + GOOGLE_OAUTH_CLIENT_SECRET
+ SESSION_SECRET (scripts/write_auth_secrets.py arma el [auth] de secrets.toml al arrancar).
"""
import streamlit as st


def habilitado() -> bool:
    """True si Streamlit tiene login configurado y es una version que lo soporta."""
    if not hasattr(st, "login"):
        return False
    try:
        auth = st.secrets["auth"]
        return bool(auth.get("client_id") and auth.get("client_secret") and auth.get("cookie_secret"))
    except Exception:
        return False


def esta_logueado() -> bool:
    try:
        return bool(st.user.get("is_logged_in", False))
    except Exception:
        return False


def email_verificado() -> str | None:
    """Mail de la cuenta de Google, solo si Google lo marca como verificado."""
    try:
        if not st.user.get("email_verified", False):
            return None
        return str(st.user.get("email") or "").strip().lower() or None
    except Exception:
        return None


def cerrar() -> bool:
    """Cierra la sesion de Google si la hay. Devuelve True si hizo st.logout() (que ya re-ejecuta)."""
    if esta_logueado():
        st.logout()
        return True
    return False
