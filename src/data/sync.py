"""Sync Google Sheets -> PostgreSQL (espejo de medica, nutricion, fisica y partidos).

Uso:  py -m src.data.sync [--source medica|nutricion|fisica_base_test|partidos|partido:<n>] [--dry-run]
      py -m src.data.sync --loop --every 300     (worker: Procfile `worker:`)

- UNA llamada values.batchGet por spreadsheet (+ 1 de metadatos).
- Upsert idempotente en sheet_rows por (source,row_num) segun row_hash; borra filas
  que ya no existen (solo row_num < APP_ROW_BASE: las filas que la app inserta
  directo quedan intactas). Headers originales en sheet_headers.
- Sin estado de sesion: lock con pg_try_advisory_xact_lock dentro de la transaccion
  (compatible con pgbouncer/Neon). Backoff exponencial ante 429/5xx.
- Solo LEE de Google Sheets.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

if __package__ in (None, ""):  # permite `py src/data/sync.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text

from src.data import sources as S
from src.data.db import connect
from src.data.rows import (
    APP_ROW_BASE, clean_text, find_dni_index, find_fecha_index, normalize_dni,
    pad_rows, parse_fecha, row_hash, unique_keys,
)

ALL_SOURCES = ["medica", "nutricion", "fisica_base_test", "partidos"]


# --------------------------------------------------------------------------- Google
def _with_backoff(fn, *args, retries: int = 6, **kwargs):
    from gspread.exceptions import APIError

    delay = 2.0
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except APIError as exc:
            code = getattr(getattr(exc, "response", None), "status_code", None)
            if code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(delay + random.uniform(0, 1))
                delay = min(delay * 2, 60)
                continue
            raise


def _get_client():
    from src.utils.credentials import get_gspread_client

    client = get_gspread_client()
    if client is None:
        raise RuntimeError("No hay credenciales de Google (ver src/utils/credentials.py)")
    return client


def _quote(title: str) -> str:
    return "'" + title.replace("'", "''") + "'"


def fetch_spreadsheet(client, spreadsheet_id: str, choose=None):
    """Devuelve ([titulos en orden], {titulo: values}) con 1 metadata + 1 batchGet.

    choose: callable(list[str]) -> list[str] para elegir pestanas, o None (todas).
    """
    hc = client.http_client
    meta = _with_backoff(
        hc.fetch_sheet_metadata, spreadsheet_id,
        params={"fields": "sheets.properties(title,sheetType)"},
    )
    titles = [
        s["properties"]["title"]
        for s in meta.get("sheets", [])
        if s["properties"].get("sheetType", "GRID") == "GRID"
    ]
    chosen = choose(titles) if choose else titles
    if not chosen:
        return titles, {}
    resp = _with_backoff(hc.values_batch_get, spreadsheet_id, [_quote(t) for t in chosen])
    out = {}
    for title, vr in zip(chosen, resp.get("valueRanges", [])):
        out[title] = pad_rows(vr.get("values", []) or [])
    return titles, out


def resolve_tab(titles: list[str], wanted: str | None) -> str | None:
    """Misma resolucion que areafisica._leer_hoja: exacta, flexible, o la primera."""
    if not titles:
        return None
    if wanted is None:
        return titles[0]
    if wanted in titles:
        return wanted
    norm = wanted.strip().lower().replace(" ", "")
    for t in titles:
        if t.strip().lower().replace(" ", "") == norm:
            return t
    return titles[0]


# --------------------------------------------------------------------------- DB
def build_rows(values: list[list[str]], mirror_dni: bool):
    """values (ya con padding) -> (headers, [fila jsonable])."""
    if not values:
        return [], []
    headers = [clean_text(c) for c in values[0]]
    keys = unique_keys(headers)
    dni_i = find_dni_index(headers) if mirror_dni else None
    fecha_i = find_fecha_index(headers) if mirror_dni else None
    out = []
    for n, raw in enumerate(values[1:], start=1):
        row = [clean_text(c) for c in raw]
        out.append({
            "row_num": n,
            "row_hash": row_hash(headers, row),
            "dni": normalize_dni(row[dni_i]) if dni_i is not None else None,
            "fecha": parse_fecha(row[fecha_i]) if fecha_i is not None else None,
            "data": dict(zip(keys, row)),
        })
    return headers, out


_UPSERT = text("""
INSERT INTO sheet_rows (source, row_num, row_hash, dni, fecha, data, synced_at)
SELECT :source, r.row_num, r.row_hash, r.dni, r.fecha, r.data, now()
FROM jsonb_to_recordset(CAST(:rows AS jsonb))
     AS r(row_num int, row_hash text, dni text, fecha date, data jsonb)
ON CONFLICT (source, row_num) DO UPDATE
SET row_hash = EXCLUDED.row_hash, dni = EXCLUDED.dni, fecha = EXCLUDED.fecha,
    data = EXCLUDED.data, synced_at = now()
""")

_HEADERS_UPSERT = text("""
INSERT INTO sheet_headers (source, headers, synced_at)
VALUES (:source, CAST(:headers AS jsonb), now())
ON CONFLICT (source) DO UPDATE SET headers = EXCLUDED.headers, synced_at = now()
""")


def _apply_source(conn, source: str, headers, rows, dry_run: bool,
                  fetched_at: float | None = None) -> dict:
    existing = {
        r[0]: r[1]
        for r in conn.execute(
            text("SELECT row_num, row_hash FROM sheet_rows "
                 "WHERE source = :s AND row_num < :b"),
            {"s": source, "b": APP_ROW_BASE},
        )
    }
    new_nums = {r["row_num"] for r in rows}
    changed = [r for r in rows if existing.get(r["row_num"]) != r["row_hash"]]
    inserted = sum(1 for r in changed if r["row_num"] not in existing)
    stale = [n for n in existing if n not in new_nums]
    stats = {"rows": len(rows), "inserted": inserted,
             "updated": len(changed) - inserted, "deleted": len(stale)}
    if dry_run:
        return stats
    for i in range(0, len(changed), 1000):
        conn.execute(_UPSERT, {
            "source": source,
            "rows": json.dumps(changed[i:i + 1000], ensure_ascii=False),
        })
    if stale:
        conn.execute(
            text("DELETE FROM sheet_rows WHERE source = :s AND row_num = ANY(:n)"),
            {"s": source, "n": stale},
        )
    conn.execute(_HEADERS_UPSERT,
                 {"source": source, "headers": json.dumps(headers, ensure_ascii=False)})
    if fetched_at is not None:
        # Filas que la app inserto Y ademas espejo al Sheet (MIRROR_WRITES_TO_SHEETS):
        # si el Sheet ya las tenia cuando se leyo, la copia local sobra (evita duplicados).
        conn.execute(
            text("DELETE FROM sheet_rows WHERE source = :s AND row_num >= :b "
                 "AND data->>'__mirrored__' IS NOT NULL "
                 "AND CAST(data->>'__mirrored__' AS double precision) < :t"),
            {"s": source, "b": APP_ROW_BASE, "t": fetched_at})
    return stats


def _delete_source(conn, source: str, dry_run: bool) -> int:
    n = conn.execute(text("SELECT count(*) FROM sheet_rows WHERE source=:s AND row_num < :b"),
                     {"s": source, "b": APP_ROW_BASE}).scalar() or 0
    if not dry_run:
        conn.execute(text("DELETE FROM sheet_rows WHERE source=:s AND row_num < :b"),
                     {"s": source, "b": APP_ROW_BASE})
        conn.execute(text("DELETE FROM sheet_headers WHERE source=:s"), {"s": source})
    return n


def _run_logged(label: str, dry_run: bool, work) -> dict:
    """Ejecuta work(conn)->stats en una transaccion con advisory lock + sync_runs."""
    run_id = None
    if not dry_run:
        with connect() as c:
            run_id = c.execute(
                text("INSERT INTO sync_runs (source, status) VALUES (:s, 'running') RETURNING id"),
                {"s": label}).scalar()
            c.commit()
    status, error, stats = "ok", None, {"rows": 0}
    try:
        with connect() as conn:
            got = conn.execute(text("SELECT pg_try_advisory_xact_lock(hashtext(:k))"),
                               {"k": f"sync:{label}"}).scalar()
            if not got:
                status, stats = "skipped_locked", {"rows": 0}
            else:
                stats = work(conn)
                if dry_run:
                    conn.rollback()
                else:
                    conn.commit()
    except Exception as exc:  # solo tipo y mensaje corto
        status, error = "error", f"{type(exc).__name__}: {str(exc)[:300]}"
    if run_id is not None:
        with connect() as c:
            c.execute(text("UPDATE sync_runs SET finished_at=now(), rows=:r, status=:st, "
                           "error=:e WHERE id=:i"),
                      {"r": stats.get("rows", 0), "st": status, "e": error, "i": run_id})
            c.commit()
    return {"source": label, "status": status, "error": error, **stats}


def _sync_single(client, name: str, dry_run: bool) -> dict:
    skey, tkey = S.SYNC_SOURCES[name]
    wanted = S.tab_name(tkey)
    fetched_at = time.time()
    try:
        _, vals = fetch_spreadsheet(
            client, S.sheet_id(skey),
            lambda ts: [t for t in [resolve_tab(ts, wanted)] if t])
    except Exception as exc:
        return {"source": name, "status": "error",
                "error": f"{type(exc).__name__}: {str(exc)[:300]}", "rows": 0}
    values = next(iter(vals.values()), [])
    headers, rows = build_rows(values, mirror_dni=True)
    return _run_logged(name, dry_run,
                       lambda conn: _apply_source(conn, name, headers, rows, dry_run, fetched_at))


def _sync_partidos(client, only: str | None, dry_run: bool) -> dict:
    try:
        titles, vals = fetch_spreadsheet(
            client, S.sheet_id("partidos"),
            (lambda ts: [t for t in ts if S.PARTIDO_PREFIX + t == only]) if only else None)
    except Exception as exc:
        return {"source": only or "partidos", "status": "error",
                "error": f"{type(exc).__name__}: {str(exc)[:300]}", "rows": 0}

    def work(conn):
        total = {"rows": 0, "inserted": 0, "updated": 0, "deleted": 0, "tabs": len(vals)}
        for title, values in vals.items():
            headers, rows = build_rows(values, mirror_dni=False)
            st = _apply_source(conn, S.PARTIDO_PREFIX + title, headers, rows, dry_run)
            for k in ("rows", "inserted", "updated", "deleted"):
                total[k] += st[k]
        if not only:  # sync completa: quitar pestanas que ya no existen
            current = {S.PARTIDO_PREFIX + t for t in titles}
            db_sources = [r[0] for r in conn.execute(text(
                "SELECT source FROM sheet_headers WHERE left(source, :n) = :p"),
                {"n": len(S.PARTIDO_PREFIX), "p": S.PARTIDO_PREFIX})]
            for src in db_sources:
                if src not in current:
                    total["deleted"] += _delete_source(conn, src, dry_run)
            if not dry_run:
                conn.execute(_HEADERS_UPSERT, {
                    "source": S.PARTIDOS_INDEX,
                    "headers": json.dumps(titles, ensure_ascii=False)})
        return total

    return _run_logged(only or "partidos", dry_run, work)


def run_sync(sources: list[str] | None = None, dry_run: bool = False, client=None) -> list[dict]:
    """Punto de entrada reutilizable (boton 'Sincronizar ahora')."""
    client = client or _get_client()
    results = []
    for src in (sources or ALL_SOURCES):
        if src in S.SYNC_SOURCES:
            results.append(_sync_single(client, src, dry_run))
        elif src == "partidos":
            results.append(_sync_partidos(client, None, dry_run))
        elif src.startswith(S.PARTIDO_PREFIX):
            results.append(_sync_partidos(client, src, dry_run))
        else:
            raise SystemExit(f"fuente desconocida: {src}")
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sync Google Sheets -> PostgreSQL")
    ap.add_argument("--source", action="append",
                    help="medica|nutricion|fisica_base_test|partidos|partido:<nombre> (repetible)")
    ap.add_argument("--dry-run", action="store_true", help="no escribe en la DB")
    ap.add_argument("--loop", action="store_true",
                    help="modo worker: repite la sincronizacion indefinidamente")
    ap.add_argument("--every", type=int, default=300, metavar="SEGUNDOS",
                    help="intervalo entre corridas con --loop (default 300)")
    args = ap.parse_args(argv)
    if args.loop:
        return _loop(args)
    return _once(args)


def _once(args) -> int:
    results = run_sync(args.source, args.dry_run)
    bad = 0
    for r in results:
        extra = {k: v for k, v in r.items() if k not in ("source", "status", "error")}
        print(f"{'[dry-run] ' if args.dry_run else ''}{r['source']}: {r['status']} {extra}"
              + (f" error={r['error']}" if r.get("error") else ""), flush=True)
        bad += r["status"] == "error"
    return 1 if bad else 0


def _loop(args) -> int:
    """Worker/cron: una corrida cada --every segundos. Un error no mata el proceso."""
    every = max(int(args.every), 10)
    print(f"sync worker: cada {every}s (Ctrl+C para salir)", flush=True)
    while True:
        started = time.time()
        try:
            _once(args)
        except SystemExit:
            raise
        except Exception as exc:  # DB/Google caidos: reintenta en la proxima vuelta
            print(f"sync worker: error {type(exc).__name__}: {str(exc)[:200]}", flush=True)
        try:
            time.sleep(max(1.0, every - (time.time() - started)))
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    sys.exit(main())
