"""Token de "Recordarme": firma, vencimiento, manipulacion y apagado sin secreto. Sin DB ni Sheets."""
import pytest

from src.security import remember

SECRETO = "un-secreto-de-prueba-bien-largo"


@pytest.fixture(autouse=True)
def con_secreto(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", SECRETO)


def test_roundtrip():
    t = remember.crear_token("coach")
    assert remember.validar_token(t) == "coach"


def test_vencido():
    t = remember.crear_token("coach", ahora=1_000)
    venc = 1_000 + remember.DIAS_VIGENCIA * 86400
    assert remember.validar_token(t, ahora=venc - 1) == "coach"
    assert remember.validar_token(t, ahora=venc + 1) is None


def test_manipulado():
    t = remember.crear_token("coach")
    payload, firma = t.split(".")
    otro = remember.crear_token("admin").split(".")[0]
    assert remember.validar_token(f"{otro}.{firma}") is None
    assert remember.validar_token(f"{payload}.{firma[:-2]}xx") is None
    assert remember.validar_token("basura") is None
    assert remember.validar_token("a.b.c") is None
    assert remember.validar_token(None) is None


def test_otro_secreto_invalida(monkeypatch):
    t = remember.crear_token("coach")
    monkeypatch.setenv("SESSION_SECRET", "otro-secreto-distinto-muy-largo")
    assert remember.validar_token(t) is None


def test_sin_secreto_esta_apagado(monkeypatch):
    monkeypatch.delenv("SESSION_SECRET")
    monkeypatch.setattr(remember, "_secret", lambda: None)
    assert not remember.habilitado()
    assert remember.crear_token("coach") is None
    assert remember.validar_token("x.y") is None


def test_secreto_corto_no_vale(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "corto")
    assert not remember.habilitado()


def test_js_cookie_tiene_atributos_de_seguridad():
    js = remember.js_guardar_cookie("tok")
    assert "Secure" in js and "SameSite=Lax" in js and "Max-Age=2592000" in js
    assert "Max-Age=0" in remember.js_borrar_cookie()
