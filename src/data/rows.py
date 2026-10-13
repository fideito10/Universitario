"""Utilidades puras (sin Streamlit) para filas de Sheets: claves unicas, DNI, fecha, hash."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date

# Filas escritas por la app directo en sheet_rows usan row_num >= APP_ROW_BASE;
# el sync nunca las toca.
APP_ROW_BASE = 1_000_000

_DNI_HEADERS = ["dni", "documento", "por favor completa el dni", "nro dni", "cedula"]
_DNI_FALLBACK = ["DNI", "Dni", "dni", "Por Favor completa el Dni", "documento"]
_FECHA_HEADERS = ["marca temporal", "timestamp", "fecha", "fecha del reporte", "fecha de carga"]


def unique_keys(headers: list[str]) -> list[str]:
    """Claves unicas para el jsonb: duplicados -> 'nombre_2', vacios -> '__blank__N'."""
    seen: set[str] = set()
    out: list[str] = []
    blanks = 0
    for h in headers:
        h = "" if h is None else str(h)
        if h.strip() == "":
            blanks += 1
            base = f"__blank__{blanks}"
        else:
            base = h
        key, n = base, 1
        while key in seen:
            n += 1
            key = f"{base}_{n}"
        seen.add(key)
        out.append(key)
    return out


def pad_rows(values: list[list[str]]) -> list[list[str]]:
    """Igual que gspread fill_gaps: rellena con '' hasta el ancho maximo."""
    width = max((len(r) for r in values), default=0)
    return [list(map(str, r)) + [""] * (width - len(r)) for r in values]


def find_dni_index(headers: list[str]) -> int | None:
    """Misma logica que dashboard_360.buscar_columna_dni, sobre una lista de headers."""
    lowered: dict[str, int] = {}
    for i, h in enumerate(headers):
        lowered[str(h).strip().lower()] = i  # como el dict de la original: gana la ultima
    for p in _DNI_HEADERS:
        if p in lowered:
            return lowered[p]
    for c in _DNI_FALLBACK:
        if c in headers:
            return headers.index(c)
    return None


def find_fecha_index(headers: list[str]) -> int | None:
    lowered: dict[str, int] = {}
    for i, h in enumerate(headers):
        lowered.setdefault(str(h).strip().lower(), i)
    for p in _FECHA_HEADERS:
        if p in lowered:
            return lowered[p]
    return None


def normalize_dni(value) -> str | None:
    """Solo digitos; '12345678.0' -> '12345678'. Vacio/sin digitos -> None."""
    if value is None:
        return None
    s = str(value).strip()
    s = re.sub(r"^(\d+)[.,]0+$", r"\1", s)
    digits = re.sub(r"\D", "", s)
    return digits or None


_DATE_RE = re.compile(r"^\s*(\d{1,4})[/-](\d{1,2})[/-](\d{1,4})")


def parse_fecha(value) -> str | None:
    """Devuelve 'YYYY-MM-DD' o None. Soporta dd/mm/yyyy[ hh:mm] y yyyy-mm-dd."""
    if not value:
        return None
    m = _DATE_RE.match(str(value))
    if not m:
        return None
    a, b, c = (int(x) for x in m.groups())
    try:
        if a > 31:  # yyyy-mm-dd
            d = date(a, b, c)
        elif c > 31:  # dd/mm/yyyy
            d = date(c, b, a)
        else:
            return None
    except ValueError:
        return None
    return d.isoformat()


def clean_text(s: str) -> str:
    return s.replace("\x00", "")


def row_hash(headers: list[str], row: list[str]) -> str:
    payload = json.dumps([headers, row], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()
