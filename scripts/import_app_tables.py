"""Importacion UNICA e idempotente: Jugadores_Maestro, Usuarios, Wellness_Jugador -> Postgres.

Uso:  py scripts/import_app_tables.py [--dry-run] [--force]

- Lee del Sheet central con UNA llamada batchGet (solo lectura).
- Si una tabla destino ya tiene datos NO la toca (la DB ya es fuente de verdad);
  --force la reemplaza completa desde el Sheet.
- Conserva la fila cruda en `extra` (todas las columnas originales, strings) y los
  headers en sheet_headers (source app:<tabla>) para que repo.df_* devuelvan lo mismo
  que get_all_records(). La clave se guarda tal cual con clave_es_hash=false.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from src.data import sources as S  # noqa: E402
from src.data.db import connect  # noqa: E402
from src.data.rows import clean_text, normalize_dni, parse_fecha, unique_keys  # noqa: E402
from src.data.sync import _get_client, fetch_spreadsheet  # noqa: E402

_LOCK = "import_app_tables"


def _num(v):
    s = str(v).strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _records(values):
    """values -> (headers, [ (dict_por_clave_unica) ])."""
    if not values:
        return [], []
    headers = [clean_text(c) for c in values[0]]
    keys = unique_keys(headers)
    return headers, [dict(zip(keys, [clean_text(c) for c in r])) for r in values[1:]]


def _g(rec: dict, *names):
    for n in names:
        if n in rec:
            return rec[n].strip()
    return ""


def build_jugadores(recs):
    out = []
    for i, r in enumerate(recs):
        out.append({
            "orden": i, "dni": normalize_dni(_g(r, "DNI", "Dni", "dni")),
            "nombre": _g(r, "Nombre"), "apellido": _g(r, "Apellido"),
            "categoria": _g(r, "Categoria"), "posicion": _g(r, "Posicion"),
            "estado": _g(r, "Estado"), "extra": r,
        })
    return out


def build_usuarios(recs):
    out, seen, dups = [], set(), 0
    for i, r in enumerate(recs):
        u = _g(r, "Usuario")
        if not u or u in seen:
            dups += 1
            continue
        seen.add(u)
        out.append({
            "orden": i, "usuario": u, "clave_hash": r.get("Clave", ""),
            "rol": _g(r, "Rol"), "nombre": _g(r, "Nombre"),
            "dni": normalize_dni(_g(r, "DNI")), "email": _g(r, "Email"), "extra": r,
        })
    return out, dups


def build_wellness(recs):
    out = []
    for i, r in enumerate(recs):
        out.append({
            "orden": i, "dni": normalize_dni(_g(r, "DNI")),
            "fecha": parse_fecha(_g(r, "Fecha")),
            "rpe": _num(_g(r, "RPE")), "sueno": _num(_g(r, "Sueno")),
            "doms": _num(_g(r, "DOMS")), "score": _num(_g(r, "Wellness_Score")),
            "nombre": _g(r, "Nombre_Jugador"), "email": _g(r, "Email_Jugador"), "extra": r,
        })
    return out


_INSERT = {
    "jugadores": """
        INSERT INTO jugadores (dni, nombre, apellido, categoria, posicion, estado, extra, orden)
        SELECT r.dni, r.nombre, r.apellido, r.categoria, r.posicion, r.estado, r.extra, r.orden
        FROM jsonb_to_recordset(CAST(:rows AS jsonb)) AS r(dni text, nombre text, apellido text,
             categoria text, posicion text, estado text, extra jsonb, orden int)""",
    "usuarios": """
        INSERT INTO usuarios (usuario, clave_hash, clave_es_hash, rol, nombre, dni, email,
                              extra, orden)
        SELECT r.usuario, r.clave_hash, false, r.rol, r.nombre, r.dni, r.email, r.extra, r.orden
        FROM jsonb_to_recordset(CAST(:rows AS jsonb)) AS r(usuario text, clave_hash text,
             rol text, nombre text, dni text, email text, extra jsonb, orden int)""",
    "wellness": """
        INSERT INTO wellness (dni, fecha, rpe, sueno, doms, score, nombre, email, extra, orden)
        SELECT r.dni, r.fecha, r.rpe, r.sueno, r.doms, r.score, r.nombre, r.email, r.extra, r.orden
        FROM jsonb_to_recordset(CAST(:rows AS jsonb)) AS r(dni text, fecha date, rpe numeric,
             sueno numeric, doms numeric, score numeric, nombre text, email text,
             extra jsonb, orden int)""",
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="reemplaza las tablas aunque ya tengan datos")
    args = ap.parse_args(argv)

    tabs = {k: S.tab_name(k) for k in ("jugadores", "usuarios", "wellness")}
    _, vals = fetch_spreadsheet(_get_client(), S.sheet_id("central"),
                                lambda ts: [t for t in tabs.values() if t in ts])
    missing = [k for k, t in tabs.items() if t not in vals]
    if missing:
        print(f"ERROR: faltan pestanas en el central: {missing}", file=sys.stderr)
        return 1

    parsed = {}
    for key in tabs:
        headers, recs = _records(vals[tabs[key]])
        parsed[key] = (headers, recs)
    jug = build_jugadores(parsed["jugadores"][1])
    usu, usu_skipped = build_usuarios(parsed["usuarios"][1])
    wel = build_wellness(parsed["wellness"][1])
    plan = {"jugadores": jug, "usuarios": usu, "wellness": wel}

    print("Origen (Sheet): " + ", ".join(f"{k}={len(parsed[k][1])}" for k in plan))
    print(f"Usuarios omitidos (vacios/duplicados): {usu_skipped}")
    print(f"Jugadores sin DNI valido: {sum(1 for j in jug if not j['dni'])}")

    with connect() as conn:
        if not conn.execute(text("SELECT pg_try_advisory_xact_lock(hashtext(:k))"),
                            {"k": _LOCK}).scalar():
            print("ERROR: otra importacion en curso", file=sys.stderr)
            return 1
        for key, rows in plan.items():
            have = conn.execute(text(f"SELECT count(*) FROM {key}")).scalar()
            if have and not args.force:
                print(f"{key}: ya tiene {have} filas en DB, se omite (use --force para reemplazar)")
                continue
            if args.dry_run:
                print(f"[dry-run] {key}: se importarian {len(rows)} filas (DB tiene {have})")
                continue
            if have:
                conn.execute(text(f"DELETE FROM {key}"))
            if rows:
                conn.execute(text(_INSERT[key]),
                             {"rows": json.dumps(rows, ensure_ascii=False)})
            conn.execute(text(
                "INSERT INTO sheet_headers (source, headers, synced_at) "
                "VALUES (:s, CAST(:h AS jsonb), now()) "
                "ON CONFLICT (source) DO UPDATE SET headers=EXCLUDED.headers, synced_at=now()"),
                {"s": f"app:{key}", "h": json.dumps(parsed[key][0], ensure_ascii=False)})
            print(f"{key}: importadas {len(rows)} filas")
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
