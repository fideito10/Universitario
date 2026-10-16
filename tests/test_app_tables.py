"""Fase 4: datos propios de la app en PostgreSQL (usuarios, jugadores, wellness, asistencias).

- Login (admin de emergencia, usuario/clave, DNI de jugador, clave incorrecta, re-hash en
  el primer login y login posterior con hash) y escrituras: en un schema TEMPORAL; no
  tocan `public`.
- Paridad de lectura contra Sheets en vivo (solo lectura). Las diferencias se reportan con
  indices/columnas, nunca con valores.
"""
import json
import sys
import uuid
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_backend import _ambos, _modo  # noqa: E402
from test_parity import _have_db, _have_google, diff_frames  # noqa: E402

needs_db = pytest.mark.skipif(not _have_db(), reason="requiere DATABASE_URL")
needs_live = pytest.mark.skipif(not (_have_google() and _have_db()),
                                reason="requiere credenciales de Google y DATABASE_URL")


# --------------------------------------------------------------------------- hash (sin DB)
def test_hash_roundtrip():
    from src.security import passwords as p
    h = p.hash_password("clave123")
    assert h.startswith("scrypt$16384$8$1$") and h.count("$") == 5 and p.is_hash(h)
    assert p.verify_password("clave123", h)
    assert not p.verify_password("otra", h)
    assert not p.verify_password("clave123", "no-es-hash")
    assert p.hash_password("clave123") != h  # sal aleatoria
    assert not p.is_hash("admin123")


# --------------------------------------------------------------------------- fixture schema
@pytest.fixture
def pg(monkeypatch):
    """Schema temporal con las migraciones; repo_app.connect apunta a ese schema."""
    from src.data import db, repo_app
    from src.data.migrate import apply_migrations

    name = "test_" + uuid.uuid4().hex[:10]
    with db.connect() as conn:
        apply_migrations(conn, schema=name)
        conn.commit()

    class _Conn:
        def __enter__(self):
            self.c = db.connect()
            self.c.exec_driver_sql(f'SET search_path TO "{name}"')
            return self.c

        def __exit__(self, *a):
            try:
                self.c.rollback()
                self.c.exec_driver_sql("RESET search_path")
                self.c.commit()
            finally:
                self.c.close()

    monkeypatch.setattr(repo_app, "connect", lambda: _Conn())

    def run(sql, **params):
        with _Conn() as c:
            r = c.execute(text(sql), params)
            out = r.all() if r.returns_rows else None
            c.commit()
            return out

    run.schema = name
    yield run
    with db.connect() as conn:
        conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{name}" CASCADE')
        conn.commit()


def _seed(run, usuarios=(), jugadores=()):
    """usuarios: (usuario, clave, rol, nombre, dni). jugadores: (dni, nombre, apellido, cat, estado)."""
    heads = {"app:usuarios": ["Usuario", "Clave", "Rol", "Nombre", "DNI", "Email"],
             "app:jugadores": ["DNI", "Nombre", "Apellido", "Posicion", "Categoria",
                               "Fecha_Nacimiento", "Fecha_Alta", "Estado", "Email", "Telefono",
                               "Temporada"],
             "app:wellness": ["ID", "Timestamp", "Email_Jugador", "Nombre_Jugador", "RPE", "Sueno",
                              "DOMS", "Wellness_Score", "Fecha"]}
    for s, h in heads.items():
        run("INSERT INTO sheet_headers (source, headers) VALUES (:s, CAST(:h AS jsonb))",
            s=s, h=json.dumps(h))
    for i, (u, c, rol, nom, dni) in enumerate(usuarios):
        run("INSERT INTO usuarios (usuario, clave_hash, clave_es_hash, rol, nombre, dni, orden, extra) "
            "VALUES (:u, :c, false, :r, :n, :d, :o, CAST(:e AS jsonb))",
            u=u, c=c, r=rol, n=nom, d=dni or None, o=i,
            e=json.dumps({"Usuario": u, "Clave": c, "Rol": rol, "Nombre": nom, "DNI": dni, "Email": ""}))
    for i, (dni, nom, ape, cat, est) in enumerate(jugadores):
        e = {"DNI": dni, "Nombre": nom, "Apellido": ape, "Posicion": "Pilar", "Categoria": cat,
             "Fecha_Nacimiento": "01/01/2000", "Fecha_Alta": "01/01/2024", "Estado": est,
             "Email": "", "Telefono": "", "Temporada": "2024"}
        run("INSERT INTO jugadores (dni, nombre, apellido, categoria, posicion, estado, extra, orden) "
            "VALUES (:d, :n, :a, :c, 'Pilar', :s, CAST(:e AS jsonb), :o)",
            d=dni, n=nom, a=ape, c=cat, s=est, e=json.dumps(e), o=i)


# --------------------------------------------------------------------------- login
class _SS(dict):
    __getattr__ = dict.get

    def __setattr__(self, k, v):
        self[k] = v


class _FakeSt:
    def __init__(self):
        self.session_state = _SS()
        self.msgs = []

    def error(self, m, *a, **k):
        self.msgs.append(("error", str(m)))

    def warning(self, m, *a, **k):
        self.msgs.append(("warning", str(m)))


@pytest.fixture
def auth(monkeypatch, pg):
    from src.security import auth as auth_mod

    monkeypatch.setenv("DATA_BACKEND", "postgres")
    fake = _FakeSt()
    monkeypatch.setattr(auth_mod, "st", fake)
    am = auth_mod.AuthManager.__new__(auth_mod.AuthManager)
    am.gs_manager = type("G", (), {"credentials_loaded": False, "client": None})()
    am.sheet_id = "x"
    am.worksheet_name = "Usuarios"
    _seed(pg,
          usuarios=[("coach", "pass 1", "Entrenador", "Coach Uno", ""),
                    ("jug1", "9999", "Jugador", "Jugador Uno", "30.111.222")],
          jugadores=[("40111222", "Ana", "Perez", "Primera", "Activo"),
                     ("40111222", "Dup", "Licado", "Primera", "Activo"),
                     ("", "Sin", "Dni", "Primera", "Activo")])
    return am, fake, pg


@needs_db
def test_login_admin_fallback_sin_db(monkeypatch, auth):
    am, fake, pg = auth
    from src.data import repo_app
    monkeypatch.setattr(repo_app, "connect", lambda: (_ for _ in ()).throw(RuntimeError("db caida")))
    assert am.login(" ADMIN ", " admin123 ") is True
    assert fake.session_state.user == {"username": "admin", "rol": "Administrador",
                                       "nombre": "Admin Sistema", "dni": ""}


@needs_db
def test_login_usuario_rehash_y_login_posterior(auth):
    am, fake, pg = auth
    assert am.login("coach", "otra") is False
    assert fake.session_state.get("authenticated") is None
    assert pg("SELECT clave_es_hash FROM usuarios WHERE usuario='coach'") == [(False,)]

    assert am.login(" coach ", " pass 1 ") is True  # coincidencia exacta con strip
    u = fake.session_state.user
    assert (u["username"], u["rol"], u["nombre"], u["dni"]) == ("coach", "Entrenador", "Coach Uno", "")
    h, es_hash, extra = pg("SELECT clave_hash, clave_es_hash, extra FROM usuarios WHERE usuario='coach'")[0]
    assert es_hash is True and h.startswith("scrypt$") and "pass 1" not in h
    assert extra["Clave"] == ""  # no queda el texto plano

    fake.session_state.clear()
    assert am.login("coach", "pass 1") is True  # login con clave hasheada
    assert am.login("coach", "pass 2") is False
    assert am.login("COACH", "pass 1") is False  # el usuario es exacto
    # el hash no cambia por loguearse otra vez (no re-hashea hashes)
    assert pg("SELECT clave_hash FROM usuarios WHERE usuario='coach'")[0][0] == h
    # el df que ve el resto de la app conserva columnas/orden del Sheet
    assert list(am._get_users_df().columns)[:6] == ["Usuario", "Clave", "Rol", "Nombre", "DNI", "Email"]


@needs_db
def test_login_dni_jugador(auth):
    am, fake, pg = auth
    # A. DNI presente en Usuarios con rol Jugador (puntos en el DNI guardado)
    assert am.login("30111222", "30111222") is True
    assert fake.session_state.user["username"] == "jug1" and fake.session_state.user["rol"] == "Jugador"
    # B. DNI en Jugadores_Maestro (usuario y clave iguales, o clave vacia)
    fake.session_state.clear()
    assert am.login("40.111.222", "40111222") is True
    assert fake.session_state.user == {"username": "40111222", "rol": "Jugador",
                                       "nombre": "Ana Perez", "dni": "40111222"}
    fake.session_state.clear()
    assert am.login("40111222", "") is True
    # DNI inexistente: mismo mensaje que con Sheets
    fake.session_state.clear()
    assert am.login("11111111", "11111111") is False
    assert ("warning", "⚠️ DNI 11111111 no encontrado en la base de jugadores.") in fake.msgs
    # DNI distinto en usuario y clave no es login por DNI
    assert am.login("40111222", "40111223") is False


# --------------------------------------------------------------------------- escrituras
@needs_db
def test_jugadores_alta_estado_y_duplicados(pg):
    from src.data import repo_app as r
    _seed(pg, jugadores=[("40111222", "Ana", "Perez", "Primera", "Activo"),
                         ("40111222", "Dup", "Licado", "Primera", "Activo"),
                         ("", "Sin", "Dni", "Primera", "Activo")])
    base = r.df_jugadores()
    assert len(base) == 3 and list(base.columns)[:3] == ["DNI", "Nombre", "Apellido"]
    assert list(base.columns)[-1] == "Temporada"

    pd_ = {"dni": "12.345.678", "nombre": "Juan", "apellido": "Gomez", "posicion": "Wing",
           "categoria": "Reserva", "fecha_nacimiento": date(2001, 2, 3), "email": "j@x.com",
           "telefono": "11"}
    assert r.dni_existe("12345678") is False
    r.agregar_jugador(pd_)
    assert r.dni_existe("12345678") and r.dni_existe(12345678)
    with pytest.raises(r.DniExistente):
        r.agregar_jugador(pd_)
    df = r.df_jugadores()
    assert len(df) == 4 and list(df.columns) == list(base.columns)
    nuevo = df.iloc[-1]  # al final, como un append_row
    assert nuevo["DNI"] == "12.345.678" and nuevo["Estado"] == "Activo"
    assert nuevo["Fecha_Nacimiento"] == "03/02/2001" and nuevo["Temporada"] == ""
    assert nuevo["Categoria"] == "Reserva" and nuevo["Posicion"] == "Wing"

    # estado: solo el PRIMER jugador con ese DNI (como update_cell sobre la primera coincidencia)
    assert r.actualizar_estado_jugador("40111222", "Lesionado") == 1
    df = r.df_jugadores()
    assert list(df["Estado"][:3]) == ["Lesionado", "Activo", "Activo"]
    assert pg("SELECT estado FROM jugadores ORDER BY orden LIMIT 1") == [("Lesionado",)]
    assert r.actualizar_estado_jugador("99999999", "Activo") == 0
    assert r.actualizar_estado_jugador("", "Suspendido") == 1  # DNI vacio


@needs_db
def test_wellness_alta(pg):
    from src.data import repo_app as r
    _seed(pg)
    assert r.leer_wellness().empty
    for i in range(2):
        r.agregar_wellness(timestamp=f"2026-10-1{i} 08:00:00", email="N/A", nombre="Ana Perez",
                           rpe=5, sueno=4, doms=2, score=4.17, fecha=f"2026-10-1{i}", dni="40111222")
    df = r.leer_wellness()
    assert list(df.columns) == ["ID", "Timestamp", "Email_Jugador", "Nombre_Jugador", "RPE",
                                "Sueno", "DOMS", "Wellness_Score", "Fecha"]
    assert list(df["ID"]) == [1, 2] and list(df["RPE"]) == [5, 5]
    assert df["Wellness_Score"].iloc[0] == 4.17 and df["Fecha"].iloc[1] == "2026-10-11"
    assert pg("SELECT fecha::text, rpe, dni FROM wellness ORDER BY id")[0] == ("2026-10-10", 5, "40111222")


@needs_db
def test_asistencias_alta_y_lectura(pg):
    from src.data import repo_app as r
    assert r.leer_asistencias().empty  # como una hoja sin filas
    filas = [["05/10/2026", "Primera", "Entrenamiento", "40111222", "Ana", "Perez", "Presente", ""],
             ["05/10/2026", "Primera", "Entrenamiento", "40111223", "Beto", "Diaz", "Ausente", "tarde"]]
    assert r.agregar_asistencias(filas) == 2 and r.agregar_asistencias([]) == 0
    df = r.leer_asistencias()
    assert list(df.columns) == ["Fecha", "Categoria", "Tipo_Actividad", "DNI", "Nombre", "Apellido",
                                "Estado_Asistencia", "Observaciones"]
    assert list(df["Estado_Asistencia"]) == ["Presente", "Ausente"]
    assert list(df["DNI"]) == [40111222, 40111223]  # numericise como get_all_records
    # el reporte de Lista.py parsea 'Fecha' con dd/mm/YYYY
    assert pd.to_datetime(df["Fecha"], format="%d/%m/%Y").iloc[0] == pd.Timestamp(2026, 10, 5)
    assert pg("SELECT fecha::text, dni, jugador FROM asistencias ORDER BY id")[1] == \
        ("2026-10-05", "40111223", "Beto Diaz")


@needs_db
def test_sync_no_toca_tablas_de_la_app():
    from src.data import sync
    assert not {"usuarios", "jugadores", "wellness", "asistencias"} & set(sync.ALL_SOURCES)
    src = (ROOT / "src" / "data" / "sync.py").read_text(encoding="utf-8")
    for t in ("usuarios", "jugadores", "wellness", "asistencias", "app:"):
        assert f"FROM {t}" not in src and f"INTO {t}" not in src and f"UPDATE {t}" not in src
    assert "app:" not in src


# --------------------------------------------------------------------------- paridad (Sheets en vivo)
@needs_live
def test_paridad_jugadores_y_loaders(monkeypatch):
    from src.modules.administracion import JugadoresMaestroManager
    a, b = _ambos(monkeypatch, lambda: JugadoresMaestroManager()._fetch_players())
    assert not a.empty and diff_frames(a, b) == []
    a, b = _ambos(monkeypatch, lambda: JugadoresMaestroManager().get_all_players())
    assert diff_frames(a, b) == []


@needs_live
def test_paridad_dashboard_central(monkeypatch):
    from src.modules.dashboard_360 import obtener_df_central
    a, b = _ambos(monkeypatch, obtener_df_central)
    assert not a.empty and diff_frames(a, b) == []


@needs_live
def test_paridad_conectar_base_central(monkeypatch):
    from src.modules import areanutricion, reportemedico
    for fn in (areanutricion.conectar_base_central, reportemedico.conectar_base_central):
        a, b = _ambos(monkeypatch, fn)
        assert a and a == b, fn.__module__


@needs_live
def test_paridad_usuarios(monkeypatch):
    from src.security.auth import AuthManager
    a, b = _ambos(monkeypatch, lambda: AuthManager()._get_users_df())
    assert not a.empty
    b = b.drop(columns=["Clave_Es_Hash"])
    assert diff_frames(a, b) == []


@needs_live
def test_paridad_wellness(monkeypatch):
    from src.modules import wellness
    sid = "1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw"
    a, b = _ambos(monkeypatch, lambda: _leer_wellness_sin_cache(wellness, sid))
    assert diff_frames(a, b) == []
    a, b = _ambos(monkeypatch, lambda: _leer_maestro_sin_cache(wellness, sid))
    assert diff_frames(a, b) == []


def _leer_wellness_sin_cache(mod, sid):
    from src.sheets.google_sheets_manager import get_sheets_manager
    mod._leer_wellness.clear()
    return mod._leer_wellness(sid, get_sheets_manager())


def _leer_maestro_sin_cache(mod, sid):
    from src.sheets.google_sheets_manager import get_sheets_manager
    mod._leer_maestro.clear()
    return mod._leer_maestro(sid, get_sheets_manager())
