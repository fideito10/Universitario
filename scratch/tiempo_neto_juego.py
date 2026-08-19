"""
tiempo_neto_juego.py
---------------------
Estima el tiempo neto de juego (balon en juego) de un partido a partir del
CSV de decodificacion (Nacsport/SportsCode), uniendo los intervalos
Start-Stop de TODAS las categorias/acciones en una sola linea de tiempo.

Metodo:
  1. Se leen todas las filas de todas las categorias del CSV.
  2. Cada fila aporta un intervalo [Start, Stop] (tiempo de video).
  3. Se unen (merge) los intervalos que se solapan o se tocan -> tramos
     continuos de juego "activo" (con acciones tageadas).
  4. Los huecos entre tramos son paradas (touch, penal, lesion, entretiempo).
  5. El hueco mas largo se reporta aparte como "entretiempo" estimado.

Limitacion: el Start/Stop de cada clip suele tener 1-3s de colchon antes y
despues de la accion real, asi que esto es una aproximacion (tiende a
sobreestimar levemente el tiempo neto real).

Uso:
    python scratch/tiempo_neto_juego.py "015 San Andres - 015 CULP (san andres) (0-0) PRIMERA A  2026.csv"
"""

import sys
import os
import re

CSV_DEFAULT = "015 San Andres - 015 CULP (san andres) (0-0) PRIMERA A  2026.csv"

# Categorias que no representan una accion de juego real (alineacion, etc.)
CATEGORIAS_EXCLUIR = {"Sustituciones", "PERSONAL (*)"}


def parse_csv(filepath: str) -> dict:
    sections = {}
    current_cat = None
    current_headers = []
    with open(filepath, encoding="utf-8-sig") as f:
        for raw_line in f:
            line = raw_line.rstrip("\r\n")
            if line.startswith("CATEGORY:"):
                current_cat = line.replace("CATEGORY:", "").split(";")[0].strip()
                sections[current_cat] = {"headers": [], "rows": []}
                current_headers = []
                continue
            if current_cat is None:
                continue
            cols = [c.strip() for c in line.split(";")]
            if all(c == "" for c in cols):
                current_cat = None
                continue
            if not current_headers:
                if cols[0].lower() == "name":
                    sections[current_cat]["headers"] = cols
                    current_headers = cols
                continue
            padded = cols + [""] * (len(current_headers) - len(cols))
            row = dict(zip(current_headers, padded[:len(current_headers)]))
            sections[current_cat]["rows"].append(row)
    return sections


def time_to_seconds(t: str) -> float:
    """Convierte 'M:SS,mmm' o 'H:MM:SS,mmm' a segundos (float)."""
    t = t.strip().replace(",", ".")
    parts = t.split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h = 0
        m, s = parts
    else:
        raise ValueError(f"Formato de tiempo inesperado: {t}")
    return h * 3600 + m * 60 + s


def seconds_to_clock(s: float) -> str:
    s = max(0, s)
    m = int(s // 60)
    sec = s - m * 60
    return f"{m}:{sec:05.2f}"


def merge_intervals(intervals):
    intervals = sorted(intervals)
    merged = []
    for start, stop in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], stop))
        else:
            merged.append((start, stop))
    return merged


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else CSV_DEFAULT
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), csv_path)

    if not os.path.exists(csv_path):
        print(f"No se encontro el archivo: {csv_path}")
        sys.exit(1)

    data = parse_csv(csv_path)

    intervals = []
    for cat, content in data.items():
        if cat in CATEGORIAS_EXCLUIR:
            continue
        for row in content["rows"]:
            start_raw = row.get("Start", "")
            stop_raw = row.get("Stop", "")
            if not start_raw or not stop_raw:
                continue
            try:
                start = time_to_seconds(start_raw)
                stop = time_to_seconds(stop_raw)
            except ValueError:
                continue
            if stop <= start:
                continue
            intervals.append((start, stop))

    if not intervals:
        print("No se encontraron intervalos Start/Stop validos.")
        sys.exit(1)

    merged = merge_intervals(intervals)

    total_video_span = merged[-1][1] - merged[0][0]
    net_play_time = sum(stop - start for start, stop in merged)

    gaps = []
    for i in range(1, len(merged)):
        gap_start = merged[i - 1][1]
        gap_stop = merged[i][0]
        gaps.append((gap_stop - gap_start, gap_start, gap_stop))

    gaps_sorted = sorted(gaps, reverse=True)
    entretiempo = gaps_sorted[0] if gaps_sorted else None
    otras_paradas = gaps_sorted[1:] if len(gaps_sorted) > 1 else []
    dead_time_total = sum(g[0] for g in gaps)
    dead_time_sin_entretiempo = dead_time_total - (entretiempo[0] if entretiempo else 0)

    print("=" * 60)
    print(f"Archivo: {os.path.basename(csv_path)}")
    print("=" * 60)
    print(f"Acciones tageadas consideradas : {len(intervals)}")
    print(f"Tramos continuos de juego       : {len(merged)}")
    print()
    print(f"Ventana total de video           : {seconds_to_clock(total_video_span)}  ({total_video_span/60:.1f} min)")
    print(f"Tiempo neto de juego (aprox.)    : {seconds_to_clock(net_play_time)}  ({net_play_time/60:.1f} min)")
    print(f"Tiempo muerto total              : {seconds_to_clock(dead_time_total)}  ({dead_time_total/60:.1f} min)")
    if entretiempo:
        print()
        print(f"Entretiempo estimado (hueco mas largo): {entretiempo[0]/60:.1f} min"
              f"  [{seconds_to_clock(entretiempo[1])} -> {seconds_to_clock(entretiempo[2])}]")
        print(f"Tiempo muerto sin contar entretiempo  : {seconds_to_clock(dead_time_sin_entretiempo)}"
              f"  ({dead_time_sin_entretiempo/60:.1f} min)")

    print()
    print(f"Top 10 paradas mas largas (excluyendo entretiempo):")
    for dur, gs, ge in otras_paradas[:10]:
        print(f"  {dur:6.1f}s   [{seconds_to_clock(gs)} -> {seconds_to_clock(ge)}]")

    print()
    print(f"Cantidad de paradas (excl. entretiempo) : {len(otras_paradas)}")
    if otras_paradas:
        print(f"Duracion promedio de parada              : {sum(d for d,_,_ in otras_paradas)/len(otras_paradas):.1f}s")


if __name__ == "__main__":
    main()
