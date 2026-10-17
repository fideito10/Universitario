"""Entrar con Google: ingreso por mail registrado y armado del [auth] de secrets.toml. Sin DB ni Google."""
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest
import streamlit as st

from src.security import auth

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def am(monkeypatch):
    a = object.__new__(auth.AuthManager)  # sin tocar Google Sheets
    df = pd.DataFrame([
        {"Usuario": "coach", "Clave": "x", "Rol": "Entrenador", "Nombre": "Seba", "DNI": "", "Email": "Coach@Club.com "},
        {"Usuario": "sinmail", "Clave": "x", "Rol": "Entrenador", "Nombre": "N", "DNI": "", "Email": ""},
    ])
    monkeypatch.setattr(auth.AuthManager, "_get_users_df", lambda self: df)
    monkeypatch.setattr(auth, "use_postgres", lambda: False)
    st.session_state.clear()
    return a


def test_mail_registrado_entra_sin_importar_mayusculas(am):
    assert am.login_by_email("COACH@club.com") is True
    assert st.session_state.authenticated is True
    assert st.session_state.user["username"] == "coach"
    assert st.session_state.user["rol"] == "Entrenador"


def test_mail_no_registrado_no_entra(am):
    assert am.login_by_email("intruso@gmail.com") is False
    assert not st.session_state.get("authenticated", False)


def test_mail_vacio_no_entra_ni_matchea_usuarios_sin_mail(am):
    assert am.login_by_email("") is False
    assert am.login_by_email(None) is False
    assert not st.session_state.get("authenticated", False)


def _cargar_script():
    spec = importlib.util.spec_from_file_location("write_auth_secrets", RAIZ / "scripts" / "write_auth_secrets.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_escribe_auth(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "id123")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "sec456")
    monkeypatch.setenv("SESSION_SECRET", "un-secreto-de-prueba-bien-largo")
    monkeypatch.setenv("RAILWAY_PUBLIC_DOMAIN", "app.example.com")
    _cargar_script().main()
    txt = (tmp_path / ".streamlit" / "secrets.toml").read_text()
    assert "[auth]" in txt and 'client_id = "id123"' in txt
    assert 'redirect_uri = "https://app.example.com/oauth2callback"' in txt
    assert "un-secreto-de-prueba" not in txt  # el cookie_secret es derivado, no el secreto crudo


def test_script_no_pisa_secrets_existentes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".streamlit").mkdir()
    previo = '[gcp]\nx = "1"\n\n[auth]\nclient_id = "viejo"\n'
    (tmp_path / ".streamlit" / "secrets.toml").write_text(previo)
    for k, v in {"GOOGLE_OAUTH_CLIENT_ID": "nuevo", "GOOGLE_OAUTH_CLIENT_SECRET": "s",
                 "SESSION_SECRET": "un-secreto-de-prueba-bien-largo", "RAILWAY_PUBLIC_DOMAIN": "a.b"}.items():
        monkeypatch.setenv(k, v)
    _cargar_script().main()
    assert (tmp_path / ".streamlit" / "secrets.toml").read_text() == previo


def test_script_agrega_auth_sin_borrar_lo_demas(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".streamlit").mkdir()
    (tmp_path / ".streamlit" / "secrets.toml").write_text('[gcp]\nx = "1"\n')
    for k, v in {"GOOGLE_OAUTH_CLIENT_ID": "id", "GOOGLE_OAUTH_CLIENT_SECRET": "s",
                 "SESSION_SECRET": "un-secreto-de-prueba-bien-largo", "RAILWAY_PUBLIC_DOMAIN": "a.b"}.items():
        monkeypatch.setenv(k, v)
    _cargar_script().main()
    txt = (tmp_path / ".streamlit" / "secrets.toml").read_text()
    assert '[gcp]\nx = "1"' in txt and "[auth]" in txt


def test_script_apagado_sin_variables(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for k in ("GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET", "SESSION_SECRET"):
        monkeypatch.delenv(k, raising=False)
    _cargar_script().main()
    assert not (tmp_path / ".streamlit" / "secrets.toml").exists()
