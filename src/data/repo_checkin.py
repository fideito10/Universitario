"""Check-in por QR: celulares vinculados a un DNI y registro de 'Presente' en asistencias.

Sin Streamlit. Mismo patron que repo_app (`conn=None` abre y confirma; con `conn` el
llamador maneja la transaccion, asi los tests usan un schema temporal).
"""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

from src.data import repo_app
from src.data.repo_app import _use
from src.data.rows import normalize_dni, parse_fecha

MAX_DISPOSITIVOS = 2
TIPO_DEFAULT = "Entrenamiento"
_ESTADOS_BAJA = {"inactivo", "baja", "retirado"}

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/Argentina/Buenos_Aires")
except Exception:  # sin tzdata (p. ej. Windows): Argentina no tiene horario de verano
    _TZ = timezone(timedelta(hours=-3))


class LimiteDispositivos(Exception):
    """El DNI ya tiene MAX_DISPOSITIVOS celulares vinculados."""


def ahora() -> datetime:
    return datetime.now(_TZ)


def hash_token(token: str) -> str:
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- jugador
def verificar_jugador(dni, nacimiento, conn=None) -> dict | None:
    """Jugador activo cuyo DNI y fecha de nacimiento coinciden; None si no.

    Si el jugador no tiene fecha de nacimiento cargada NO se puede vincular (el staff debe
    completarla): sin segundo dato, el DNI solo lo sabe cualquiera.
    """
    n = normalize_dni(dni)
    nac = parse_fecha(nacimiento)
    if not n or not nac:
        return None
    with _use(conn) as c:
        row = c.execute(text(
            "SELECT nombre, apellido, categoria, estado, extra->>'Fecha_Nacimiento' "
            "FROM jugadores WHERE dni = :d ORDER BY orden, id LIMIT 1"), {"d": n}).first()
    if row is None:
        return None
    nombre, apellido, categoria, estado, nac_guardada = row
    if parse_fecha(nac_guardada) != nac:
        return None
    if str(estado or "").strip().lower() in _ESTADOS_BAJA:
        return None
    return {"dni": n, "nombre": nombre or "", "apellido": apellido or "",
            "categoria": categoria or ""}


def datos_jugador(dni, conn=None) -> dict | None:
    n = normalize_dni(dni)
    if not n:
        return None
    with _use(conn) as c:
        row = c.execute(text(
            "SELECT nombre, apellido, categoria FROM jugadores WHERE dni = :d "
            "ORDER BY orden, id LIMIT 1"), {"d": n}).first()
    if row is None:
        return None
    return {"dni": n, "nombre": row[0] or "", "apellido": row[1] or "", "categoria": row[2] or ""}


# --------------------------------------------------------------------------- dispositivos
def vincular_dispositivo(dni, etiqueta: str = "", conn=None) -> str:
    """Crea un token nuevo para el DNI y devuelve el token en claro (solo se muestra aca)."""
    n = normalize_dni(dni)
    token = secrets.token_urlsafe(32)
    with _use(conn) as c:
        c.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"disp:{n}"})
        activos = c.execute(text(
            "SELECT count(*) FROM dispositivos WHERE dni = :d AND revoked_at IS NULL"),
            {"d": n}).scalar()
        if activos >= MAX_DISPOSITIVOS:
            raise LimiteDispositivos(n)
        c.execute(text(
            "INSERT INTO dispositivos (dni, token_hash, etiqueta, last_seen) "
            "VALUES (:d, :h, :e, now())"),
            {"d": n, "h": hash_token(token), "e": (etiqueta or "")[:200]})
    return token


def dni_de_token(token, conn=None) -> str | None:
    """DNI del celu con ese token (y marca last_seen); None si no existe o fue revocado."""
    if not token:
        return None
    with _use(conn) as c:
        row = c.execute(text(
            "UPDATE dispositivos SET last_seen = now() "
            "WHERE token_hash = :h AND revoked_at IS NULL RETURNING dni"),
            {"h": hash_token(token)}).first()
    return row[0] if row else None


def dispositivos_de(dni, conn=None) -> list[dict]:
    n = normalize_dni(dni)
    with _use(conn) as c:
        rows = c.execute(text(
            "SELECT etiqueta, created_at, last_seen FROM dispositivos "
            "WHERE dni = :d AND revoked_at IS NULL ORDER BY id"), {"d": n}).all()
    return [{"etiqueta": r[0], "alta": r[1], "ultimo_uso": r[2]} for r in rows]


def revocar_dispositivos(dni, conn=None) -> int:
    """Desvincula todos los celus del DNI (el jugador vuelve a vincular con DNI + nacimiento)."""
    n = normalize_dni(dni)
    with _use(conn) as c:
        return c.execute(text(
            "UPDATE dispositivos SET revoked_at = now() WHERE dni = :d AND revoked_at IS NULL"),
            {"d": n}).rowcount


# --------------------------------------------------------------------------- presente
def registrar_presente(dni, tipo: str = TIPO_DEFAULT, conn=None) -> tuple[str, dict | None]:
    """Marca 'Presente' hoy para el DNI. Devuelve (resultado, jugador).

    resultado: 'nuevo' | 'repetido' (ya estaba presente) | 'inexistente' (DNI sin jugador).
    Si el entrenador ya lo habia cargado como Ausente/Lesionado hoy, se corrige a Presente
    en esa misma fila (no queda duplicado).
    """
    n = normalize_dni(dni)
    ahora_ = ahora()
    hoy = ahora_.date()
    obs = f"QR {ahora_:%H:%M}"
    with _use(conn) as c:
        jug = datos_jugador(n, conn=c)
        if jug is None:
            return "inexistente", None
        c.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"chk:{n}:{hoy}"})
        row = c.execute(text(
            "SELECT id, estado FROM asistencias WHERE dni = :d AND fecha = :f "
            "AND extra->>'Tipo_Actividad' = :t ORDER BY id LIMIT 1"),
            {"d": n, "f": hoy, "t": tipo}).first()
        if row is not None and (row[1] or "").strip().lower() == "presente":
            return "repetido", jug
        if row is not None:
            c.execute(text(
                "UPDATE asistencias SET estado = 'Presente', "
                "extra = extra || CAST(:x AS jsonb) WHERE id = :i"),
                {"i": row[0], "x": json.dumps(
                    {"Estado_Asistencia": "Presente", "Observaciones": obs}, ensure_ascii=False)})
            return "nuevo", jug
        repo_app.agregar_asistencias([[
            hoy.strftime("%d/%m/%Y"), jug["categoria"], tipo, n,
            jug["nombre"], jug["apellido"], "Presente", obs]], conn=c)
    return "nuevo", jug


def presentes_hoy(tipo: str = TIPO_DEFAULT, fecha: date | None = None, conn=None) -> list[dict]:
    f = fecha or ahora().date()
    with _use(conn) as c:
        rows = c.execute(text(
            "SELECT dni, jugador, categoria, extra->>'Observaciones' FROM asistencias "
            "WHERE fecha = :f AND lower(estado) = 'presente' AND extra->>'Tipo_Actividad' = :t "
            "ORDER BY id"), {"f": f, "t": tipo}).all()
    return [{"DNI": r[0], "Jugador": r[1], "Categoria": r[2], "Registro": r[3]} for r in rows]
