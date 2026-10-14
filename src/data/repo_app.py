"""Datos PROPIOS de la app en PostgreSQL (Fase 4): usuarios, jugadores, wellness, asistencias.

Lectura: devuelve el MISMO DataFrame que hoy devuelven los loaders de Sheets
(`pd.DataFrame(ws.get_all_records())`): columnas y orden = headers originales
(`sheet_headers`, source `app:<tabla>`), valores numericos convertidos como gspread.
La fila cruda vive en `extra` (clave = header unico) y el orden en `orden`/`id`.

Escritura: transaccional y sin estado de sesion (pgbouncer): `pg_advisory_xact_lock`
para serializar el calculo de `orden`. `conn=None` abre una conexion y confirma;
con `conn` el llamador maneja la transaccion (tests con schema temporal).
No importa Streamlit.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime

import pandas as pd
from sqlalchemy import text

from src.data.db import connect
from src.data.rows import normalize_dni, parse_fecha, unique_keys

# Headers por defecto (si la DB todavia no tiene `app:<tabla>` en sheet_headers).
JUGADORES_HEADERS = ["DNI", "Nombre", "Apellido", "Posicion", "Categoria", "Fecha_Nacimiento",
                     "Fecha_Alta", "Estado", "Email", "Telefono"]
USUARIOS_HEADERS = ["Usuario", "Clave", "Rol", "Nombre", "DNI", "Email"]
WELLNESS_HEADERS = ["ID", "Timestamp", "Email_Jugador", "Nombre_Jugador", "RPE", "Sueno",
                    "DOMS", "Wellness_Score", "Fecha"]
ASISTENCIAS_HEADERS = ["Fecha", "Categoria", "Tipo_Actividad", "DNI", "Nombre", "Apellido",
                       "Estado_Asistencia", "Observaciones"]

_DEFAULTS = {"jugadores": JUGADORES_HEADERS, "usuarios": USUARIOS_HEADERS,
             "wellness": WELLNESS_HEADERS, "asistencias": ASISTENCIAS_HEADERS}
_ORDER = {"jugadores": "orden, id", "usuarios": "orden, id", "wellness": "orden, id",
          "asistencias": "id"}


class DniExistente(ValueError):
    """El DNI ya esta cargado en jugadores."""


@contextmanager
def _use(conn):
    """Conexion propia (commit al salir sin error) o la del llamador (sin commit)."""
    if conn is not None:
        yield conn
        return
    with connect() as c:
        yield c
        c.commit()


def _headers(conn, table: str) -> list[str]:
    h = conn.execute(text("SELECT headers FROM sheet_headers WHERE source = :s"),
                     {"s": f"app:{table}"}).scalar()
    return list(h) if h else list(_DEFAULTS[table])


def _num(v):
    s = str(v).strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# --------------------------------------------------------------------------- lectura
def _records(conn, table: str, with_clave: bool = False) -> list[dict]:
    """Equivalente a ws.get_all_records(): numericise como gspread, orden de headers."""
    from gspread.utils import numericise_all

    # Una sola consulta (headers + filas): cada ida y vuelta a la DB cuesta ~300-400 ms.
    hq = "(SELECT headers FROM sheet_headers WHERE source = :s) AS h"
    cols = "extra, clave_hash, clave_es_hash" if table == "usuarios" else "extra"
    res = conn.execute(text(
        f"SELECT {hq}, {cols} FROM {table} ORDER BY {_ORDER[table]}"), {"s": f"app:{table}"}).all()
    h = list(res[0][0]) if res and res[0][0] else list(_DEFAULTS[table])
    keys = unique_keys(h)
    rows = [(r[1], r[2], r[3]) if table == "usuarios" else (r[1], None, None) for r in res]
    out = []
    for extra, clave_hash, es_hash in rows:
        extra = extra or {}
        vals = numericise_all([str(extra.get(k, "")) for k in keys], False, "", False, None)
        rec = dict(zip(h, vals))
        if table == "usuarios":
            # `extra` no conserva la clave tras el re-hash: la verdad es clave_hash.
            if "Clave" in rec:
                rec["Clave"] = clave_hash if clave_hash is not None else ""
            if with_clave:
                rec["Clave_Es_Hash"] = bool(es_hash)
        out.append(rec)
    return out


def df_jugadores(conn=None) -> pd.DataFrame:
    with _use(conn) as c:
        return pd.DataFrame(_records(c, "jugadores"))


def jugadores_str(conn=None) -> list[dict]:
    """Registros de Jugadores_Maestro como strings (como get_all_values + headers)."""
    with _use(conn) as c:
        res = c.execute(text(
            "SELECT (SELECT headers FROM sheet_headers WHERE source = 'app:jugadores') AS h, extra "
            f"FROM jugadores ORDER BY {_ORDER['jugadores']}")).all()
    h = list(res[0][0]) if res and res[0][0] else list(JUGADORES_HEADERS)
    keys = unique_keys(h)
    return [{col: str((r[1] or {}).get(k, "")) for col, k in zip(h, keys)} for r in res]


def leer_wellness(conn=None) -> pd.DataFrame:
    with _use(conn) as c:
        return pd.DataFrame(_records(c, "wellness"))


def leer_asistencias(conn=None) -> pd.DataFrame:
    """Vacio sin columnas si no hay filas (igual que una hoja con solo headers)."""
    with _use(conn) as c:
        return pd.DataFrame(_records(c, "asistencias"))


def usuarios_df(conn=None, con_estado_clave: bool = False) -> pd.DataFrame:
    """Tabla Usuarios. `Clave` = clave_hash (texto plano o hash segun `clave_es_hash`).

    con_estado_clave=True agrega la columna booleana `Clave_Es_Hash` (la usa el login).
    """
    with _use(conn) as c:
        return pd.DataFrame(_records(c, "usuarios", with_clave=con_estado_clave))


# --------------------------------------------------------------------------- usuarios
def actualizar_clave(usuario: str, clave_hash: str, conn=None) -> int:
    """Guarda el hash de un usuario cuya clave seguia en texto plano. Devuelve filas."""
    with _use(conn) as c:
        return c.execute(text(
            "UPDATE usuarios SET clave_hash = :h, clave_es_hash = true, "
            "extra = jsonb_set(extra, '{Clave}', '\"\"'::jsonb) "
            "WHERE usuario = :u AND clave_es_hash = false"),
            {"h": clave_hash, "u": usuario}).rowcount


# --------------------------------------------------------------------------- jugadores
def dni_existe(dni, conn=None) -> bool:
    n = normalize_dni(dni)
    if n is None:
        return False
    with _use(conn) as c:
        return c.execute(text("SELECT 1 FROM jugadores WHERE dni = :d LIMIT 1"),
                         {"d": n}).first() is not None


def agregar_jugador(player_data: dict, conn=None) -> int:
    """Alta de jugador (mismos valores que la fila que hoy se agrega al Sheet).

    Lanza DniExistente si el DNI ya esta cargado. Devuelve el `id` nuevo.
    """
    dni_raw = str(player_data["dni"])
    nac = player_data.get("fecha_nacimiento")
    valores = {
        "DNI": dni_raw,
        "Nombre": player_data["nombre"],
        "Apellido": player_data["apellido"],
        "Posicion": player_data["posicion"],
        "Categoria": player_data["categoria"],
        "Fecha_Nacimiento": nac.strftime("%d/%m/%Y") if hasattr(nac, "strftime") else str(nac or ""),
        "Fecha_Alta": datetime.now().strftime("%d/%m/%Y"),
        "Estado": "Activo",
        "Email": player_data.get("email", ""),
        "Telefono": player_data.get("telefono", ""),
    }
    with _use(conn) as c:
        c.execute(text("SELECT pg_advisory_xact_lock(hashtext('ins:jugadores'))"))
        if dni_existe(dni_raw, conn=c):
            raise DniExistente(dni_raw)
        h = _headers(c, "jugadores")
        keys = unique_keys(h)
        extra = {k: str(valores.get(col, "")) for col, k in zip(h, keys)}
        return c.execute(text(
            "INSERT INTO jugadores (dni, nombre, apellido, categoria, posicion, estado, extra, orden) "
            "SELECT :dni, :nombre, :apellido, :cat, :pos, 'Activo', CAST(:extra AS jsonb), "
            "COALESCE(MAX(orden), -1) + 1 FROM jugadores RETURNING id"),
            {"dni": normalize_dni(dni_raw), "nombre": valores["Nombre"],
             "apellido": valores["Apellido"], "cat": valores["Categoria"],
             "pos": valores["Posicion"],
             "extra": json.dumps(extra, ensure_ascii=False)}).scalar()


def actualizar_estado_jugador(dni, estado: str, conn=None) -> int:
    """Cambia el estado del PRIMER jugador con ese DNI (como el Sheet). 0 = no encontrado."""
    n = normalize_dni(dni)
    where = "dni = :d" if n else "(dni IS NULL OR dni = '')"
    with _use(conn) as c:
        c.execute(text("SELECT pg_advisory_xact_lock(hashtext('ins:jugadores'))"))
        row = c.execute(text(
            f"SELECT id FROM jugadores WHERE {where} ORDER BY orden, id LIMIT 1"),
            {"d": n}).first()
        if row is None:
            return 0
        return c.execute(text(
            "UPDATE jugadores SET estado = :e, updated_at = now(), "
            "extra = jsonb_set(extra, '{Estado}', to_jsonb(CAST(:e AS text))) WHERE id = :i"),
            {"e": estado, "i": row[0]}).rowcount


# --------------------------------------------------------------------------- wellness
def agregar_wellness(*, timestamp: str, email: str, nombre: str, rpe, sueno, doms, score,
                     fecha: str, dni=None, conn=None) -> int:
    """Una fila de Wellness_Jugador. `ID` replica el del Sheet (filas + 1)."""
    with _use(conn) as c:
        c.execute(text("SELECT pg_advisory_xact_lock(hashtext('ins:wellness'))"))
        h = _headers(c, "wellness")
        keys = unique_keys(h)
        n, orden = c.execute(text(
            "SELECT count(*), COALESCE(MAX(orden), -1) + 1 FROM wellness")).one()
        valores = {"ID": n + 1, "Timestamp": timestamp, "Email_Jugador": email,
                   "Nombre_Jugador": nombre, "RPE": rpe, "Sueno": sueno, "DOMS": doms,
                   "Wellness_Score": score, "Fecha": fecha}
        extra = {k: str(valores.get(col, "")) for col, k in zip(h, keys)}
        return c.execute(text(
            "INSERT INTO wellness (dni, fecha, rpe, sueno, doms, score, nombre, email, extra, orden) "
            "VALUES (:dni, CAST(:fecha AS date), :rpe, :sueno, :doms, :score, :nombre, :email, "
            "CAST(:extra AS jsonb), :orden) RETURNING id"),
            {"dni": normalize_dni(dni), "fecha": parse_fecha(fecha), "rpe": _num(rpe),
             "sueno": _num(sueno), "doms": _num(doms), "score": _num(score),
             "nombre": nombre, "email": email, "orden": orden,
             "extra": json.dumps(extra, ensure_ascii=False)}).scalar()


# --------------------------------------------------------------------------- asistencias
def agregar_asistencias(filas: list[list], conn=None) -> int:
    """Inserta N filas [Fecha(dd/mm/YYYY), Categoria, Tipo_Actividad, DNI, Nombre, Apellido,
    Estado_Asistencia, Observaciones] en una sola transaccion. Devuelve cuantas."""
    if not filas:
        return 0
    params = []
    for f in filas:
        f = (list(map(lambda v: "" if v is None else str(v), f)) + [""] * 8)[:8]
        params.append({
            "fecha": parse_fecha(f[0]), "cat": f[1], "dni": normalize_dni(f[3]),
            "jug": f"{f[4]} {f[5]}".strip(), "estado": f[6],
            "extra": json.dumps(dict(zip(ASISTENCIAS_HEADERS, f)), ensure_ascii=False),
        })
    with _use(conn) as c:
        c.execute(text(
            "INSERT INTO asistencias (fecha, categoria, dni, jugador, estado, extra) "
            "VALUES (CAST(:fecha AS date), :cat, :dni, :jug, :estado, CAST(:extra AS jsonb))"),
            params)
    return len(params)
