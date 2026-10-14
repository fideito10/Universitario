"""Repositorio de lectura desde PostgreSQL: mismas salidas que los loaders de Sheets.

Cada funcion replica EXACTAMENTE el tratamiento del loader original (Fase 3 solo
cambia el origen de datos):

  df_medica()            <- areamedica.create_dataframe_from_sheet  (pd.DataFrame(list[dict]))
  df_nutricion()         <- areanutricion.read_google_sheet_as_df   (sin columnas 'Unnamed')
  df_fisica_base_test()  <- areafisica._leer_hoja / cargar_hoja     (limpia, unicas, sin blancas)
  rows_partido(nombre)   <- worksheet.get_all_values()              (list[list[str]])
  lista_partidos()       <- [ws.title for ws in sh.worksheets()]
  df_jugadores/usuarios/wellness <- pd.DataFrame(ws.get_all_records())

Sin mutar nada y sin cache (la capa de cache se agrega en la Fase 3). No importa Streamlit.
Si la fuente no esta sincronizada devuelve vacio, igual que un Sheet vacio.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.data import sources as S
from src.data.db import connect
from src.data.rows import unique_keys


# --------------------------------------------------------------------------- acceso
def _load_raw(source: str) -> tuple[list[str], list[list[str]]]:
    """(headers, filas) tal como estaban en el Sheet (strings, ancho uniforme)."""
    # Una sola consulta (headers + filas): cada viaje a Neon cuesta ~0.3 s desde lejos
    with connect() as conn:
        res = conn.execute(text(
            "SELECT h.headers, r.data FROM sheet_headers h "
            "LEFT JOIN sheet_rows r ON r.source = h.source "
            "WHERE h.source = :s ORDER BY r.row_num"), {"s": source}).all()
    if not res:
        return [], []
    h = res[0][0]
    keys = unique_keys(h)
    data = [r[1] for r in res if r[1] is not None]
    width = len(h)
    rows = []
    for d in data:
        r = [str(d.get(k, "")) for k in keys]
        rows.append(r + [""] * (width - len(r)))
    return list(h), rows


def _all_values(source: str) -> list[list[str]]:
    """Equivalente a get_all_values(): [] si la hoja esta vacia."""
    headers, rows = _load_raw(source)
    if not headers and not rows:
        return []
    return [headers] + rows


# --------------------------------------------------------------------------- Sheets espejados
def df_medica() -> pd.DataFrame:
    """Como create_dataframe_from_sheet: dicts por fila (duplicados colapsan) -> DataFrame.

    Hoja vacia -> DataFrame vacio (el original devuelve None; los callers ya lo tratan
    como vacio).
    """
    values = _all_values("medica")
    if not values:
        return pd.DataFrame()
    columns = values[0]
    structured = []
    for row in values[1:]:
        structured.append({c: (row[i] if i < len(row) else "") for i, c in enumerate(columns)})
    return pd.DataFrame(structured)


def df_nutricion() -> pd.DataFrame:
    data = _all_values("nutricion")
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]


def df_fisica_base_test() -> pd.DataFrame:
    all_data = _all_values("fisica_base_test")
    if not all_data:
        return pd.DataFrame()

    def clean_value(val):
        if pd.isna(val):
            return val
        s = str(val).strip()
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
            s = s[1:-1].strip()
        return s

    def make_unique_columns(cols):
        seen, unique = {}, []
        for col in cols:
            col = clean_value(col)
            base = "__blank__" if col == "" else col
            if base in seen:
                seen[base] += 1
                unique.append(f"{base}_{seen[base]}")
            else:
                seen[base] = 0
                unique.append(base)
        return unique

    headers = make_unique_columns(all_data[0])
    data_rows = [[clean_value(c) for c in row] for row in all_data[1:]]
    df = pd.DataFrame(data_rows, columns=headers)
    drop = [c for c in df.columns if str(c).strip() == "" or str(c).startswith("__blank__")]
    if drop:
        df = df.drop(columns=drop)
    return df


# --------------------------------------------------------------------------- Partidos
def rows_partido(nombre: str) -> list[list[str]]:
    return _all_values(S.PARTIDO_PREFIX + nombre)


def todos_los_partidos() -> dict[str, list[list[str]]]:
    """Todas las pestanas de partidos en UNA consulta: {nombre: get_all_values()}.

    Evita 1 consulta por partido (23 viajes a la DB al abrir el analisis en frio).
    """
    prefijo = S.PARTIDO_PREFIX
    with connect() as conn:
        res = conn.execute(text(
            "SELECT h.source, h.headers, r.data FROM sheet_headers h "
            "LEFT JOIN sheet_rows r ON r.source = h.source "
            "WHERE h.source LIKE :p ORDER BY h.source, r.row_num"),
            {"p": prefijo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"}).all()
    out: dict[str, list[list[str]]] = {}
    keys_por_fuente: dict[str, list[str]] = {}
    for source, headers, data in res:
        nombre = source[len(prefijo):]
        h = list(headers)
        if nombre not in out:
            out[nombre] = [h]
            keys_por_fuente[nombre] = unique_keys(h)
        if data is not None:
            r = [str(data.get(k, "")) for k in keys_por_fuente[nombre]]
            out[nombre].append(r + [""] * (len(h) - len(r)))
    return out


def lista_partidos() -> list[str]:
    """Titulos de pestana en el orden del Sheet."""
    with connect() as conn:
        h = conn.execute(text("SELECT headers FROM sheet_headers WHERE source = :s"),
                         {"s": S.PARTIDOS_INDEX}).scalar()
    return list(h or [])


# --------------------------------------------------------------------------- Tablas de la app
def _records(table: str) -> list[dict]:
    """Equivalente a ws.get_all_records(): valores numericos convertidos como gspread."""
    from gspread.utils import numericise_all

    with connect() as conn:
        h = conn.execute(text("SELECT headers FROM sheet_headers WHERE source = :s"),
                         {"s": f"app:{table}"}).scalar()
        if h is None:
            return []
        extras = conn.execute(
            text(f"SELECT extra FROM {table} ORDER BY orden, id"),
        ).scalars().all()
    keys = unique_keys(h)
    out = []
    for e in extras:
        vals = numericise_all([str(e.get(k, "")) for k in keys], False, "", False, None)
        out.append(dict(zip(h, vals)))
    return out


def df_jugadores() -> pd.DataFrame:
    return pd.DataFrame(_records("jugadores"))


def df_usuarios() -> pd.DataFrame:
    return pd.DataFrame(_records("usuarios"))


def df_wellness() -> pd.DataFrame:
    return pd.DataFrame(_records("wellness"))
