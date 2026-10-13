"""Vuelca todas las pestanas de los Sheets del inventario a data_snapshot/.

Uso: py scripts/export_snapshot.py
Requiere credenciales de Google (.streamlit/secrets.toml, JSON de cuenta de
servicio o variables de entorno; ver src/utils/credentials.py).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.sources import sheet_id as _sid  # noqa: E402

# Inventario real verificado (ver src/data/sources.py)
SHEETS = {k: _sid(k) for k in
          ("central", "medica", "nutricion", "fisica", "partidos", "legacy_car")}


def _safe(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip() or "_"


def _client():
    try:
        from src.utils.credentials import get_gspread_client

        client = get_gspread_client()
        if client is not None:
            return client
    except Exception:
        pass
    try:
        import gspread
        from src.utils.credentials import get_service_account_credentials

        creds = get_service_account_credentials()
        if creds is not None:
            return gspread.authorize(creds)
    except Exception:
        pass
    return None


def main() -> int:
    client = _client()
    if client is None:
        print(
            "ERROR: no se encontraron credenciales de Google. Configure "
            ".streamlit/secrets.toml, un JSON de cuenta de servicio o las "
            "variables de entorno (ver src/utils/credentials.py).",
            file=sys.stderr,
        )
        return 1

    out_root = ROOT / "data_snapshot"
    failures = 0
    for label, sheet_id in SHEETS.items():
        try:
            ss = client.open_by_key(sheet_id)
        except Exception as exc:
            print(f"[{label}] no se pudo abrir: {type(exc).__name__}", file=sys.stderr)
            failures += 1
            continue
        out_dir = out_root / label
        out_dir.mkdir(parents=True, exist_ok=True)
        for ws in ss.worksheets():
            try:
                values = ws.get_all_values()
            except Exception as exc:
                print(f"[{label}] {ws.title}: error {type(exc).__name__}", file=sys.stderr)
                failures += 1
                continue
            payload = {
                "sheet": label,
                "sheet_id": sheet_id,
                "tab": ws.title,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "rows": len(values),
                "values": values,
            }
            (out_dir / f"{_safe(ws.title)}.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            print(f"[{label}] {ws.title}: {len(values)} filas")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
