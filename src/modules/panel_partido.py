import os
import re
import base64
from collections import defaultdict
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from src.utils.credentials import get_service_account_credentials

# ── Mapa de escudos ──
_ESCUDOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "Escudos")

_ESCUDO_MAP = {
    "universitario": "Universitariodelaplata.png",
    "culp":          "Universitariodelaplata.png",
    "hurling":       "Hurling.png",
    "cirano":        "San Cirano.png",
    "san cirano":    "San Cirano.png",
    "cirano":        "San Cirano.png",
    "gimnasia":      "GEBA.png",
    "olivos":        "Olivos.png",
    "pucara":        "Pucara.png",
    "pueyrredon":    "Pueyrredon.png",
    "san andres":    "San Andres.png",
    "andres":        "San Andres.png",
    "san albano":    "San Albano.png",
    "albano":        "San Albano.png",
    "san fernando":  "San Fernando.png",
    "fernando":      "San Fernando.png",
    "san luis":      "San Luis.png",
    "sanluis":       "San Luis.png",
    "lomas":         "Lomas Athletic.png",
    "francesa":      "Deportiva Francesa.png",
    "curupayti":     "Curupayti.png",
    "adf":           "Deportiva Francesa.png",
}

def _get_escudo_b64(team_name: str) -> str:
    """Devuelve el escudo en base64 para embeber en HTML, o '' si no encuentra."""
    import unicodedata
    def norm(t):
        return unicodedata.normalize('NFKD', t).encode('ASCII', 'ignore').decode('utf-8').lower().strip()
    
    key = norm(team_name)
    filename = None
    for k, v in _ESCUDO_MAP.items():
        norm_k = norm(k)
        if norm_k in key or key in norm_k:
            filename = v
            break
    if not filename:
        return ""
    path = os.path.join(_ESCUDOS_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ── MAPA DE DNI Y FOTOS ──
import unicodedata
from src.modules.dashboard_360 import crear_dataframe_integrado, normalizar_dni

@st.cache_data(ttl=600, show_spinner=False)
def _cargar_mapa_dni_nombres():
    try:
        df = crear_dataframe_integrado()
        if df.empty: return {}
        
        mapa = {}
        # Identificar columnas
        col_dni = next((c for c in df.columns if 'DNI' in c.upper() or 'DOCUMENTO' in c.upper()), None)
        col_nombre = next((c for c in df.columns if 'NOMBRE' in c.upper()), None)
        col_apellido = next((c for c in df.columns if 'APELLIDO' in c.upper()), None)
        
        if not col_dni or (not col_nombre and not col_apellido): return {}
        
        for _, row in df.iterrows():
            dni = str(row[col_dni]).replace('.0', '').strip()
            if not dni or dni.lower() == 'nan': continue
            
            n = str(row[col_nombre]).strip() if col_nombre else ''
            a = str(row[col_apellido]).strip() if col_apellido else ''
            
            def _norm(t):
                if not t: return ""
                t = t.replace("'", "").replace('"', '')
                t = unicodedata.normalize('NFKD', t).encode('ASCII', 'ignore').decode('utf-8')
                return t.lower().strip()
                
            nombres = []
            if a and n:
                nombres.append(f"{_norm(a)} {_norm(n)}")
                nombres.append(f"{_norm(n)} {_norm(a)}")
                nombres.append(_norm(a))
                nombres.append(_norm(n))
            elif a:
                nombres.append(_norm(a))
            elif n:
                nombres.append(_norm(n))
                
            for nm in nombres:
                if nm and nm not in mapa:
                    mapa[nm] = dni
        return mapa
    except:
        return {}

def _buscar_dni_por_nombre(nombre_jugador, mapa):
    if not nombre_jugador or not mapa: return None
    
    def _norm(t):
        if not t: return ""
        t = t.replace("'", "").replace('"', '')
        t = unicodedata.normalize('NFKD', t).encode('ASCII', 'ignore').decode('utf-8')
        return t.lower().strip()
        
    n = _norm(nombre_jugador)
    
    if n in mapa: return mapa[n]
    
    for k, v in mapa.items():
        if k in n or n in k:
            return v
            
    parts = n.split()
    for p in parts:
        if len(p) > 3:
            for k, v in mapa.items():
                if p in k:
                    return v
    return None

def _get_foto_b64(nombre_jugador, mapa):
    dni = _buscar_dni_por_nombre(nombre_jugador, mapa)
    if not dni: return ""
    
    # buscar en assets/fotos_jugadores
    import os, base64
    fotos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fotos_jugadores")
    path = os.path.join(fotos_dir, f"{dni}.jpeg")
    if not os.path.exists(path):
        path = os.path.join(fotos_dir, f"{dni}.jpg")
        if not os.path.exists(path):
            path = os.path.join(fotos_dir, f"{dni}.png")
            if not os.path.exists(path): return ""
            
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

def _player_card_html(nombre, stat_label, stat_value, color, mapa_dni):
    foto_b64 = _get_foto_b64(nombre, mapa_dni)
    img_html = f'<img src="data:image/jpeg;base64,{foto_b64}" style="width:85px;height:85px;border-radius:50%;object-fit:cover;border:3px solid {color};margin-bottom:10px;box-shadow:0 4px 8px rgba(0,0,0,0.3);"/>' if foto_b64 else f'<div style="width:85px;height:85px;border-radius:50%;background:#1c2030;border:3px solid {color};margin-bottom:10px;display:flex;align-items:center;justify-content:center;font-size:28px;color:#8b949e;box-shadow:0 4px 8px rgba(0,0,0,0.3)">👤</div>'
    
    return f'''
    <div style="background:#161b22; border:1px solid #30363d; border-radius:12px; padding:18px 12px; text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:space-between; height:100%; min-height:240px; border-top:4px solid {color}; box-shadow:0 6px 16px rgba(0,0,0,0.3)">
        <div style="display:flex; flex-direction:column; align-items:center; width:100%;">
            {img_html}
            <div style="font-size:1.15rem; font-weight:800; color:#ffffff; line-height:1.25; margin-top:8px; margin-bottom:5px; text-align:center; word-break:break-word; min-height:46px; display:flex; align-items:center; justify-content:center; width:100%;">{nombre}</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:center; width:100%;">
            <div style="font-size:2.2rem; font-weight:900; color:{color}; line-height:1; margin:8px 0 2px 0;">{stat_value}</div>
            <div style="font-size:0.8rem; color:#8b949e; text-transform:uppercase; font-weight:700; letter-spacing:1px; line-height:1.2;">{stat_label}</div>
        </div>
    </div>
    '''



_SHEET_ID = "1JXKJkDYcrOHRQ4fmC1uPkEW4crLNdJhzJLcwbMdOICU"

def _get_int(val):
    if val is None or val == "": return 0
    try:
        if isinstance(val, str): val = val.replace(',', '.')
        return int(float(val))
    except: return 0

def _clean_player(name):
    if not name: return None
    
    # Corregir codificación rota de caracteres de Google Sheets (UTF-8 interpretado como CP1252/Windows-1252)
    replacements = {
        "\u00c3\u0081": "Á",
        "\u00c3\u201c": "Ó",
        "\u00c3\u008d": "Í",
        "\u00c3\u0161": "Ú",
        "\u00c3\u2018": "Ñ",
        "\u00c3\u2030": "É",
        "\u00c3\u00a1": "á",
        "\u00c3\u00a9": "é",
        "\u00c3\u00ad": "í",
        "\u00c3\u00b3": "ó",
        "\u00c3\u00ba": "ú",
        "\u00c3\u00b1": "ñ",
    }
    name_str = str(name)
    for bad, good in replacements.items():
        name_str = name_str.replace(bad, good)
        
    name_str = name_str.strip()
    name_str = re.sub(r"^\d+[-.\s]+", "", name_str).strip()
    if not name_str or name_str.lower() in ["player", "nan", "jugador", "null"]: return None
    return name_str.title()

def _parse_sheet_data(rows_list):
    sections = {}
    current_cat = None
    current_headers = []
    for cols in rows_list:
        if not cols or not any(str(c).strip() for c in cols): continue
        cols = [str(c).strip() for c in cols]
        
        if cols[0].startswith("CATEGORY:"):
            current_cat = cols[0].replace("CATEGORY:", "").split(";")[0].strip()
            sections[current_cat] = {"headers": [], "rows": []}
            current_headers = []
            continue
        
        if current_cat is None: continue
        
        if not current_headers:
            header_keywords = ["name", "player", "equipo", "team", "jugador", "nro", "#"]
            if any(any(k in str(h).lower() for k in header_keywords) for h in cols[:4]):
                current_headers = [h.lower() for h in cols]
                sections[current_cat]["headers"] = current_headers
            continue
        
        row = dict(zip(current_headers, cols + [""] * (len(current_headers) - len(cols))))
        sections[current_cat]["rows"].append(row)
    return sections

def _get_all_matches():
    import time
    import random
    max_retries = 3
    backoff_factor = 1.5
    for attempt in range(max_retries):
        try:
            creds = get_service_account_credentials()
            if not creds: return []
            client = gspread.authorize(creds)
            sh = client.open_by_key(_SHEET_ID)
            return [ws.title for ws in sh.worksheets()]
        except Exception as e:
            err_msg = str(e)
            is_rate_limit = "429" in err_msg or "quota" in err_msg.lower() or "limit" in err_msg.lower()
            if is_rate_limit and attempt < max_retries - 1:
                time.sleep((backoff_factor ** attempt) + random.uniform(0.1, 0.5))
                continue
            else:
                return []
    return []

@st.cache_data(ttl=3600)
def _load_match_data(match_name):
    import time
    import random
    max_retries = 5
    backoff_factor = 2.0
    for attempt in range(max_retries):
        try:
            creds = get_service_account_credentials()
            if not creds:
                raise ValueError("No se pudieron obtener las credenciales de la cuenta de servicio.")
            client = gspread.authorize(creds)
            sh = client.open_by_key(_SHEET_ID)
            rows = sh.worksheet(match_name).get_all_values()
            return _parse_sheet_data(rows)
        except Exception as e:
            err_msg = str(e)
            is_rate_limit = "429" in err_msg or "quota" in err_msg.lower() or "limit" in err_msg.lower()
            if is_rate_limit and attempt < max_retries - 1:
                time.sleep((backoff_factor ** attempt) + random.uniform(0.5, 1.5))
                continue
            else:
                raise e

def _get_val(r, name):
    name_clean = name.lower().replace(" ","").replace("ó","o").replace("ó","o").replace("í","i").replace("á","a").replace("ú","u").replace("ñ","n").replace("é","e")
    for k, v in r.items():
        k_clean = k.lower().replace(" ","").replace("ó","o").replace("í","i").replace("á","a").replace("ú","u").replace("ñ","n").replace("é","e")
        if name_clean in k_clean or k_clean in name_clean:
            return _get_int(v)
    return 0

@st.cache_data(ttl=600, show_spinner=False)
def _cargar_detalles_jugadores():
    try:
        df = crear_dataframe_integrado()
        if df.empty: return {}
        
        col_dni = next((c for c in df.columns if 'DNI' in c.upper() or 'DOCUMENTO' in c.upper()), None)
        col_nombre = next((c for c in df.columns if 'NOMBRE' in c.upper()), None)
        col_apellido = next((c for c in df.columns if 'APELLIDO' in c.upper()), None)
        col_posicion = next((c for c in df.columns if 'POSICION' in c.upper() or 'POSICIÓN' in c.upper()), None)
        col_categoria = next((c for c in df.columns if 'CATEGORIA' in c.upper() or 'CATEGORÍA' in c.upper() or 'DIVISION' in c.upper()), None)
        
        detalles = {}
        for _, row in df.iterrows():
            dni = str(row[col_dni]).replace('.0', '').strip() if col_dni else ''
            if not dni or dni.lower() == 'nan': continue
            
            n = str(row[col_nombre]).strip() if col_nombre else ''
            a = str(row[col_apellido]).strip() if col_apellido else ''
            pos = str(row[col_posicion]).strip() if col_posicion else 'N/A'
            cat = str(row[col_categoria]).strip() if col_categoria else 'N/A'
            
            if pos.lower() in ['nan', 'none', '']: pos = 'N/A'
            if cat.lower() in ['nan', 'none', '']: cat = 'N/A'
            
            nombre_completo = f"{n} {a}".strip() if n and a else (n or a or f"Jugador {dni}")
            detalles[dni] = {
                "nombre": nombre_completo,
                "posicion": pos,
                "categoria": cat,
                "dni": dni
            }
        return detalles
    except:
        return {}

@st.cache_data(ttl=600, show_spinner=False)
def _get_player_historical_stats(player_name, matches_tuple, mapa_dni_tuple):
    mapa_dni = dict(mapa_dni_tuple)
    player_dni = _buscar_dni_por_nombre(player_name, mapa_dni)
    
    TEAM_LOCAL_PREFIXES = ["CULP", "UNI", "UNIVERSITARIO"]
    
    history = []
    for match_name in matches_tuple:
        try:
            match_data = _load_match_data(match_name)
        except Exception as e:
            st.warning(f"No se pudieron cargar los datos históricos del partido {match_name} ({e})")
            continue
        if not match_data: continue
        
        # 1. Puntos
        pts_rows = []
        for k in match_data.keys():
            if "PUNTOS" in k.upper():
                pts_rows.extend(match_data[k]["rows"])
        
        player_pts = 0
        tries, goals, penals, drops, try_penal = 0, 0, 0, 0, 0
        for r in pts_rows:
            is_propio = _get_int(r.get("propio"))
            is_rival = _get_int(r.get("rival"))
            if is_rival and not is_propio:
                continue
            rp = _clean_player(r.get("player") or r.get("jugador"))
            r_dni = _buscar_dni_por_nombre(rp, mapa_dni) if rp else None
            if (rp and rp.lower() == player_name.lower()) or (player_dni and r_dni == player_dni):
                t_val = _get_int(r.get("try"))
                g_val = _get_int(r.get("goal"))
                p_val = _get_int(r.get("penal"))
                d_val = _get_int(r.get("drop"))
                tp_val = _get_int(r.get("try penal"))
                
                tries += t_val
                goals += g_val
                penals += p_val
                drops += d_val
                try_penal += tp_val
                player_pts += t_val * 5 + g_val * 2 + p_val * 3 + d_val * 3 + tp_val * 7
        
        # 2. Tackles
        tck_rows = []
        for k in match_data.keys():
            if "TACKLE" in k.upper() and "RECIBIDO" not in k.upper():
                tck_rows.extend(match_data[k]["rows"])
        p_tackles, p_tackles_ok, p_tackles_fail, p_tackles_doble = 0, 0, 0, 0
        for r in tck_rows:
            r_team = r.get("team") or ""
            is_rival_team = r_team and not any(px in r_team.upper() for px in TEAM_LOCAL_PREFIXES)
            if is_rival_team:
                continue
            raw_player = r.get("player") or r.get("name") or r.get("jugador") or ""
            jugadores = [j.strip() for j in str(raw_player).split("|") if j.strip()]
            for raw_p in jugadores:
                p = _clean_player(raw_p)
                j_dni = _buscar_dni_por_nombre(p, mapa_dni) if p else None
                if (p and p.lower() == player_name.lower()) or (player_dni and j_dni == player_dni):
                    p_tackles += 1
                    p_tackles_ok += _get_int(r.get("bueno") or r.get("bien (detiene)") or r.get("ok", 0))
                    p_tackles_fail += _get_int(r.get("malo") or r.get("mal (falla)") or r.get("fail", 0))
                    p_tackles_doble += _get_int(r.get("doble tackle") or r.get("doble", 0))
                    
        # 3. Quiebres
        qbr_rows = []
        for k in match_data.keys():
            if "QUIEBRE" in k.upper() and "RIVAL" not in k.upper():
                qbr_rows.extend(match_data[k]["rows"])
        p_quiebres = 0
        for r in qbr_rows:
            r_team = r.get("team") or ""
            is_rival_team = r_team and not any(px in r_team.upper() for px in TEAM_LOCAL_PREFIXES)
            if is_rival_team:
                continue
            rp = _clean_player(r.get("player") or r.get("jugador") or r.get("name"))
            r_dni = _buscar_dni_por_nombre(rp, mapa_dni) if rp else None
            if (rp and rp.lower() == player_name.lower()) or (player_dni and r_dni == player_dni):
                p_quiebres += 1
                
        # 4. Apoyos (Móviles)
        mov_rows = []
        for k in match_data.keys():
            if "MOVILES" in k.upper():
                mov_rows.extend(match_data[k]["rows"])
        p_apoyos, p_primero, p_segundo = 0, 0, 0
        for r in mov_rows:
            is_propio = _get_int(r.get("propio"))
            r_team = r.get("team") or ""
            if is_propio or any(px in r_team.upper() for px in TEAM_LOCAL_PREFIXES) or not r_team:
                raw_p = r.get("player") or r.get("jugador") or ""
                players = [_clean_player(p.strip()) for p in raw_p.split("|") if p.strip()]
                for idx, j in enumerate(players):
                    j_dni = _buscar_dni_por_nombre(j, mapa_dni) if j else None
                    if (j and j.lower() == player_name.lower()) or (player_dni and j_dni == player_dni):
                        p_apoyos += 1
                        if idx == 0 and _get_int(r.get("1")):
                            p_primero += 1
                        if _get_int(r.get("2")):
                            if idx == 1 or (idx == 0 and len(players) == 1):
                                p_segundo += 1
                                
        # 5. Kicks
        kck_rows = []
        for k in match_data.keys():
            if "KICK" in k.upper():
                kck_rows.extend(match_data[k]["rows"])
        p_kicks, p_kicks_gana, p_kicks_err = 0, 0, 0
        for r in kck_rows:
            r_team = r.get("team") or ""
            is_rival_team = r_team and not any(px in r_team.upper() for px in TEAM_LOCAL_PREFIXES)
            if is_rival_team:
                continue
            rp = _clean_player(r.get("player") or r.get("jugador") or r.get("name"))
            r_dni = _buscar_dni_por_nombre(rp, mapa_dni) if rp else None
            if (rp and rp.lower() == player_name.lower()) or (player_dni and r_dni == player_dni):
                p_kicks += 1
                p_kicks_gana += _get_val(r, "gana terreno")
                p_kicks_err += (_get_val(r, "pelota tapada") + 
                                _get_val(r, "directo touch") + 
                                _get_val(r, "directo ingoal") + 
                                _get_val(r, "palos errados") + 
                                _get_val(r, "mala ejecucion") + 
                                _get_val(r, "penal touch"))
                                
        # 6. Pesca
        psc_rows = []
        for k in match_data.keys():
            if "PESCA" in k.upper():
                psc_rows.extend(match_data[k]["rows"])
        p_pescas, p_pescas_rec = 0, 0
        for r in psc_rows:
            r_team = r.get("team") or ""
            is_rival_team = r_team and not any(px in r_team.upper() for px in TEAM_LOCAL_PREFIXES)
            if is_rival_team:
                continue
            rp = _clean_player(r.get("player") or r.get("jugador"))
            r_dni = _buscar_dni_por_nombre(rp, mapa_dni) if rp else None
            if (rp and rp.lower() == player_name.lower()) or (player_dni and r_dni == player_dni):
                p_pescas += 1
                if _get_int(r.get("recupera", 0)) or "OK" in str(r.get("resultado","")).upper():
                    p_pescas_rec += 1
                    
        # 7. Penales
        pnl_rows = []
        for k in match_data.keys():
            if "PENAL" in k.upper():
                pnl_rows.extend(match_data[k]["rows"])
        p_penales = 0
        for r in pnl_rows:
            r_team = r.get("team") or ""
            is_rival_team = r_team and not any(px in r_team.upper() for px in TEAM_LOCAL_PREFIXES)
            if is_rival_team:
                continue
            rp = _clean_player(r.get("player") or r.get("jugador"))
            r_dni = _buscar_dni_por_nombre(rp, mapa_dni) if rp else None
            if (rp and rp.lower() == player_name.lower()) or (player_dni and r_dni == player_dni):
                p_penales += 1
                
        if p_tackles > 0 or p_quiebres > 0 or p_apoyos > 0 or player_pts > 0 or p_kicks > 0 or p_pescas > 0 or p_penales > 0:
            history.append({
                "Partido": match_name,
                "Puntos": player_pts,
                "Tries": tries,
                "Tackles": p_tackles,
                "Tackles Efectivos": p_tackles_ok,
                "Tackles Fallados": p_tackles_fail,
                "Dobles Tackles": p_tackles_doble,
                "% Tackles": round(p_tackles_ok / p_tackles * 100) if p_tackles else 0,
                "Quiebres": p_quiebres,
                "Apoyos Ruck": p_apoyos,
                "Primero Ruck": p_primero,
                "Segundo Ruck": p_segundo,
                "Kicks": p_kicks,
                "Kicks Gana Terreno": p_kicks_gana,
                "Kicks Errores": p_kicks_err,
                "Pescas": p_pescas,
                "Pescas Recuperadas": p_pescas_rec,
                "Penales Cometidos": p_penales
            })
            
    return pd.DataFrame(history)

def rugby_analysis_module():
    # ─────────────────────────────────────────────
    # LÓGICA DE PROCESAMIENTO
    # ─────────────────────────────────────────────
    
    get_int = _get_int
    clean_player = _clean_player
    parse_sheet_data = _parse_sheet_data
    get_all_matches = _get_all_matches
    load_match_data = _load_match_data
    get_val = _get_val

    # DISEÑO UI ADAPTADO AL BRANDING
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
    .stApp { background-color: #000000; }
    .rugby-panel { font-family: 'Inter', sans-serif; color: #ffffff; }
    .hero {
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
        border: 1px solid #333; border-radius: 16px; padding: 30px; margin-bottom: 25px;
        display: flex; align-items: center; gap: 20px;
    }
    .hero-title { font-size: 2.2rem; font-weight: 900; color: #ffffff; margin: 0; }
    .hero-sub { font-size: 1rem; color: #888; }
    .scoreboard {
        background: #111; border: 1px solid #333; border-radius: 20px;
        padding: 35px; text-align: center; margin-bottom: 25px;
    }
    .score-teams { display: flex; justify-content: space-around; align-items: center; }
    .team-name { font-size: 1.1rem; font-weight: 700; color: #888; text-transform: uppercase; letter-spacing: 2px; }
    .team-score { font-size: 4.5rem; font-weight: 900; margin: 10px 0; color: #ffffff; }
    .score-dash { font-size: 3rem; color: #333; }
    .score-detail { font-size: 0.85rem; color: #555; font-family: monospace; }
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-bottom: 30px; }
    .kpi-card { background: #111; border: 1px solid #222; border-radius: 12px; padding: 20px; text-align: center; }
    .kpi-value { font-size: 2.4rem; font-weight: 900; color: #ffffff; }
    .kpi-label { font-size: 0.75rem; color: #666; margin-top: 8px; text-transform: uppercase; font-weight: 700; }
    .kpi-sub { font-size: 0.85rem; color: #ffffff; margin-top: 4px; font-weight: 600; opacity: 0.8; }
    .section-header {
        font-size: 1.2rem; font-weight: 800; color: #ffffff;
        padding: 10px 0; margin: 30px 0 15px 0; border-bottom: 2px solid #222;
    }
    </style>
    """, unsafe_allow_html=True)

    matches = get_all_matches()
    with st.container():
        c1, c2 = st.columns([2, 1])
        with c1: selected_match = st.selectbox("Seleccionar Partido", matches, label_visibility="collapsed") if matches else None
        with c2:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

    if not selected_match:
        st.warning("⚠️ No se encontraron partidos.")
        return

    with st.spinner(f"Sincronizando {selected_match}..."):
        try:
            data = load_match_data(selected_match)
        except Exception as e:
            st.error(f"No se pudieron sincronizar los datos del partido {selected_match}: {e}")
            return
    
    if not data: return


    def find_rows(term):
        combined = []
        for k in data.keys():
            if term.upper() in k.upper(): combined.extend(data[k]["rows"])
        return combined

    def pct_l(n, total): return round((n / total * 100)) if total > 0 else 0

    # Procesar Puntos
    pts_rows = find_rows("PUNTOS")
    teams = list(set(r.get("team", "") for r in pts_rows if r.get("team")))
    TEAM_LOCAL = next((t for t in teams if any(x in t.upper() for x in ["CULP", "UNI", "UNIVERSITARIO"])), "LOCAL")
    TEAM_RIVAL = next((t for t in teams if t != TEAM_LOCAL), "RIVAL")
    NAME_LOCAL = "Universitario"
    # El nombre visible del rival es el partido seleccionado en la UI (nombre de la pestaña/hoja)
    # Esto soluciona los problemas de copiado/clonación de pestañas donde el analista no renombró las filas internas.
    NAME_RIVAL = selected_match.strip() if selected_match else "Rival"
    
    def calc_score(team_id):
        rows = [r for r in pts_rows if r.get("team") == team_id]
        tries = sum(get_int(r.get("try", 0)) for r in rows)
        goals = sum(get_int(r.get("goal", 0)) for r in rows)
        pens  = sum(get_int(r.get("penal", 0)) for r in rows)
        drops = sum(get_int(r.get("drop", 0)) for r in rows)
        return (tries*5 + goals*2 + pens*3 + drops*3), tries, goals, pens, drops

    s_l, t_l, g_l, p_l, d_l = calc_score(TEAM_LOCAL)
    s_r, t_r, g_r, p_r, d_r = calc_score(TEAM_RIVAL)
    res_txt = "VICTORIA" if s_l > s_r else ("DERROTA" if s_l < s_r else "EMPATE")

    # 1) TACKLES (DETALLE)
    # Cada fila = 1 evento de tackle. Player puede tener múltiples jugadores separados por "|"
    # Se cuenta: total (apariciones), efectivos (bien/detiene), fallados (mal/falla), dobles
    # Filtrar para evitar que 'TACKLES RECIBIDOS' cuente como tackles realizados
    tck_rows = []
    for k in data.keys():
        if "TACKLE" in k.upper() and "RECIBIDO" not in k.upper():
            tck_rows.extend(data[k]["rows"])
    tck_map = defaultdict(lambda: {"total": 0, "ok": 0, "fail": 0, "doble": 0})
    for r in tck_rows:
        if r.get("team") and r.get("team") != TEAM_LOCAL:
            continue
        raw_player = r.get("player") or r.get("name") or r.get("jugador") or ""
        jugadores = [j.strip() for j in str(raw_player).split("|") if j.strip()]
        for raw_p in jugadores:
            p = clean_player(raw_p)
            if p:
                tck_map[p]["total"] += 1
                tck_map[p]["ok"]    += get_int(r.get("bueno") or r.get("bien (detiene)") or r.get("ok", 0))
                tck_map[p]["fail"]  += get_int(r.get("malo") or r.get("mal (falla)") or r.get("fail", 0))
                tck_map[p]["doble"] += get_int(r.get("doble tackle") or r.get("doble", 0))
    df_tck = pd.DataFrame([{
        "Jugador": k,
        "Total": v["total"],
        "Efectivos": v["ok"],
        "Fallados": v["fail"],
        "Dobles": v["doble"],
        "% Efectividad": round(v["ok"] / v["total"] * 100) if v["total"] else 0
    } for k, v in tck_map.items()])
    total_tackles, total_buenos, pct_efectividad = 0, 0, 0
    if not df_tck.empty:
        df_tck = df_tck.sort_values("Total", ascending=False)
        total_tackles, total_buenos = int(df_tck["Total"].sum()), int(df_tck["Efectivos"].sum())
        pct_efectividad = pct_l(total_buenos, total_tackles)
    else:
        df_tck = pd.DataFrame(columns=["Jugador", "Total", "Efectivos", "Fallados", "Dobles", "% Efectividad"])

    # 2) QUIEBRES
    # Filtrar para evitar que los quiebres del rival se mezclen
    qbr_rows = []
    for k in data.keys():
        if "QUIEBRE" in k.upper() and "RIVAL" not in k.upper():
            qbr_rows.extend(data[k]["rows"])
    qbr_map = defaultdict(int)
    for r in qbr_rows:
        p = clean_player(r.get("player") or r.get("jugador") or r.get("name"))
        if p and (not r.get("team") or r.get("team") == TEAM_LOCAL): qbr_map[p] += 1
    df_qbr = pd.DataFrame([{"Jugador": k, "Quiebres": v} for k,v in qbr_map.items()])
    if not df_qbr.empty:
        df_qbr = df_qbr.sort_values("Quiebres", ascending=False)
    else:
        df_qbr = pd.DataFrame(columns=["Jugador", "Quiebres"])

    # 2b) SCRUMS
    scr_rows = find_rows("SCRUM")
    scrum_nuestros = sum(1 for r in scr_rows if r.get("team") == TEAM_LOCAL or "PROPIO" in str(r.get("quien","")).upper() or "NOSOTRO" in str(r.get("quien","")).upper() or (not r.get("team") and not r.get("quien")))
    scrum_rival    = sum(1 for r in scr_rows if r.get("team") == TEAM_RIVAL or "RIVAL" in str(r.get("quien","")).upper())
    # Si no hay distinción por team/quien, dividir el total
    if scrum_nuestros == 0 and scrum_rival == 0 and scr_rows:
        scrum_nuestros = len(scr_rows)

    # 3) KICKS
    kck_rows = find_rows("KICK")
    
    def get_val(r, name):
        name_clean = name.lower().replace(" ","").replace("ó","o").replace("ó","o").replace("í","i").replace("á","a").replace("ú","u").replace("ñ","n").replace("é","e")
        for k, v in r.items():
            k_clean = k.lower().replace(" ","").replace("ó","o").replace("í","i").replace("á","a").replace("ú","u").replace("ñ","n").replace("é","e")
            if name_clean in k_clean or k_clean in name_clean:
                return get_int(v)
        return 0

    kck_map = defaultdict(lambda: {
        "total": 0,
        "territorial": 0,
        "bajo_presion": 0,
        "a_disputar": 0,
        "otros_tipos": 0,
        "gana": 0,
        "no_gana": 0,
        "recupero": 0,
        "no_recupero": 0,
        "errores": 0
    })
    
    # Team cumulative stats
    team_kicks_stats = {
        "total": len(kck_rows),
        "territorial": 0,
        "bajo_presion": 0,
        "a_disputar": 0,
        "rastron": 0,
        "sombrero": 0,
        "pase": 0,
        "50_22": 0,
        "gana": 0,
        "no_gana": 0,
        "recupero": 0,
        "no_recupero": 0,
        "pelota_tapada": 0,
        "directo_touch": 0,
        "directo_ingoal": 0,
        "palos_errados": 0,
        "mala_ejecucion": 0,
        "penal_touch": 0
    }
    
    for r in kck_rows:
        # Sum up team-level metrics
        team_kicks_stats["territorial"] += get_val(r, "territorial")
        team_kicks_stats["bajo_presion"] += get_val(r, "bajo presion")
        team_kicks_stats["a_disputar"] += get_val(r, "a disputar")
        team_kicks_stats["rastron"] += get_val(r, "rastron")
        team_kicks_stats["sombrero"] += get_val(r, "sombrero")
        team_kicks_stats["pase"] += get_val(r, "pase")
        team_kicks_stats["50_22"] += get_val(r, "50 - 22") or get_val(r, "50-22")
        
        team_kicks_stats["gana"] += get_val(r, "gana terreno")
        team_kicks_stats["no_gana"] += get_val(r, "no gana terreno")
        team_kicks_stats["recupero"] += get_val(r, "recupero posesion")
        team_kicks_stats["no_recupero"] += get_val(r, "no recupero posesion")
        
        team_kicks_stats["pelota_tapada"] += get_val(r, "pelota tapada")
        team_kicks_stats["directo_touch"] += get_val(r, "directo touch")
        team_kicks_stats["directo_ingoal"] += get_val(r, "directo ingoal")
        team_kicks_stats["palos_errados"] += get_val(r, "palos errados")
        team_kicks_stats["mala_ejecucion"] += get_val(r, "mala ejecucion")
        team_kicks_stats["penal_touch"] += get_val(r, "penal touch")
        
        # Player level metrics
        p = clean_player(r.get("player") or r.get("jugador") or r.get("name"))
        if p and (not r.get("team") or r.get("team") == TEAM_LOCAL):
            kck_map[p]["total"] += 1
            kck_map[p]["territorial"] += get_val(r, "territorial")
            kck_map[p]["bajo_presion"] += get_val(r, "bajo presion")
            kck_map[p]["a_disputar"] += get_val(r, "a disputar")
            
            otros = (get_val(r, "rastron") + 
                     get_val(r, "sombrero") + 
                     get_val(r, "pase") + 
                     (get_val(r, "50 - 22") or get_val(r, "50-22")))
            kck_map[p]["otros_tipos"] += otros
            
            kck_map[p]["gana"] += get_val(r, "gana terreno")
            kck_map[p]["no_gana"] += get_val(r, "no gana terreno")
            kck_map[p]["recupero"] += get_val(r, "recupero posesion")
            kck_map[p]["no_recupero"] += get_val(r, "no recupero posesion")
            
            errs = (get_val(r, "pelota tapada") + 
                    get_val(r, "directo touch") + 
                    get_val(r, "directo ingoal") + 
                    get_val(r, "palos errados") + 
                    get_val(r, "mala ejecucion") + 
                    get_val(r, "penal touch"))
            kck_map[p]["errores"] += errs
            
    kck_list = []
    for k, v in kck_map.items():
        kck_list.append({
            "Jugador": k,
            "Total Kicks": v["total"],
            "Gana Terreno": v["gana"],
            "Territorial": v["territorial"],
            "Bajo Presión": v["bajo_presion"],
            "A Disputar / Cajón": v["a_disputar"],
            "Otros Tipos": v["otros_tipos"],
            "Recuperó Posesión": v["recupero"],
            "Errores": v["errores"],
            "% Efectividad": round(v["gana"] / v["total"] * 100) if v["total"] else 0
        })
        
    df_kck = pd.DataFrame(kck_list)
    if not df_kck.empty:
        df_kck = df_kck.sort_values("Total Kicks", ascending=False)
    else:
        df_kck = pd.DataFrame(columns=["Jugador", "Total Kicks", "Gana Terreno", "Territorial", "Bajo Presión", "A Disputar / Cajón", "Otros Tipos", "Recuperó Posesión", "Errores", "% Efectividad"])


    # 4) PESCA
    psc_rows = find_rows("PESCA")
    pesca_nosotros = sum(1 for r in psc_rows if "NOSOTRO" in str(r.get("quien","")).upper() or r.get("team") == TEAM_LOCAL)
    pesca_recupera = sum(1 for r in psc_rows if get_int(r.get("recupera", 0)) or "OK" in str(r.get("resultado","")).upper())
    pesca_rival = sum(1 for r in psc_rows if "RIVAL" in str(r.get("quien","")).upper() or r.get("team") == TEAM_RIVAL)
    pesca_penal_u = sum(1 for r in psc_rows if "PENAL" in str(r.get("resultado","")).upper() and (not r.get("team") or r.get("team") == TEAM_LOCAL))
    psc_jug = defaultdict(lambda: {"total": 0, "rec": 0})
    for r in psc_rows:
        p = clean_player(r.get("player") or r.get("jugador"))
        if p:
            psc_jug[p]["total"] += 1
            if get_int(r.get("recupera",0)): psc_jug[p]["rec"] += 1
    df_psc = pd.DataFrame([{"Jugador": k, "Total": v["total"], "Recupera": v["rec"]} for k,v in psc_jug.items()])
    if not df_psc.empty:
        df_psc = df_psc.sort_values("Total", ascending=False)
    else:
        df_psc = pd.DataFrame(columns=["Jugador", "Total", "Recupera"])

    # 5) PENALES
    pnl_all = find_rows("PENAL")
    pnl_u_rows = [r for r in pnl_all if not r.get("team") or r.get("team") == TEAM_LOCAL]
    pnl_u, pnl_rival = len(pnl_u_rows), len([r for r in pnl_all if r.get("team") == TEAM_RIVAL])
    pnl_total = pnl_u + pnl_rival
    causas, jug_pnl = defaultdict(int), defaultdict(int)
    for r in pnl_u_rows:
        c = r.get("causa") or r.get("motivo") or "Otros"
        causas[c] += 1
        p = clean_player(r.get("player") or r.get("jugador"))
        if p: jug_pnl[p] += 1
    df_causas = pd.DataFrame([{"Causa": k, "Total": v} for k,v in causas.items()])
    if not df_causas.empty:
        df_causas = df_causas.sort_values("Total", ascending=False)
    else:
        df_causas = pd.DataFrame(columns=["Causa", "Total"])
    df_pnl_jug = pd.DataFrame([{"Jugador": k, "Penales Cometidos": v} for k,v in jug_pnl.items()])
    if not df_pnl_jug.empty:
        df_pnl_jug = df_pnl_jug.sort_values("Penales Cometidos", ascending=False)
    else:
        df_pnl_jug = pd.DataFrame(columns=["Jugador", "Penales Cometidos"])
    total_penales, total_pescas = pnl_u, pesca_recupera
    total_enf = sum(1 for r in find_rows("FORZADO") if not r.get("team") or r.get("team") == TEAM_LOCAL)

    # 6) LINE OUT  (columnas reales de la hoja)
    lin_rows = find_rows("LINE")
    # Helpers para leer columnas con variaciones de nombre
    def _lin(r, *keys):
        for k in keys:
            for rk in r.keys():
                if k.lower() in rk.lower():
                    return get_int(r[rk])
        return 0

    lin_total     = len(lin_rows)
    lin_prop_rows = [r for r in lin_rows if _lin(r, "propio") or r.get("team") == TEAM_LOCAL]
    lin_riv_rows  = [r for r in lin_rows if _lin(r, "rival")  or r.get("team") == TEAM_RIVAL]
    # Si no hay distincion, usar todos como propios
    if not lin_prop_rows and not lin_riv_rows:
        lin_prop_rows = lin_rows

    lin_total_prop   = len(lin_prop_rows)
    lin_total_riv    = len(lin_riv_rows)

    # Resultados de NUESTROS lines
    lin_limpia   = sum(_lin(r, "pelota limpia")        for r in lin_prop_rows)
    lin_sucia    = sum(_lin(r, "pelota sucia")         for r in lin_prop_rows)
    lin_robada   = sum(_lin(r, "robada")               for r in lin_prop_rows)
    lin_perdida  = sum(_lin(r, "perdida")              for r in lin_prop_rows)
    lin_torcida  = sum(_lin(r, "torcida")              for r in lin_prop_rows)
    lin_pasada   = sum(_lin(r, "pasada")               for r in lin_prop_rows)
    lin_rapido   = sum(_lin(r, "tiro rapido", "rapido") for r in lin_prop_rows)
    lin_inf_u    = sum(_lin(r, "infracci", "para u", "infraccion para u") for r in lin_prop_rows)
    lin_inf_riv  = sum(_lin(r, "infracci", "para rival") for r in lin_prop_rows)
    # Posiciones del lanzamiento
    lin_2m   = sum(_lin(r, "2-mar", "2 mar", "2m") for r in lin_prop_rows)
    lin_4m   = sum(_lin(r, "4-may", "4 may", "4m") for r in lin_prop_rows)
    lin_6m   = sum(_lin(r, "6-jul", "6 jul", "6m") for r in lin_prop_rows)

    # Escudos en base64
    b64_local = _get_escudo_b64(NAME_LOCAL)
    b64_rival = _get_escudo_b64(NAME_RIVAL)
    img_local = f'<img src="data:image/png;base64,{b64_local}" style="height:90px;object-fit:contain;"/>' if b64_local else f'<div class="team-name">{NAME_LOCAL}</div>'
    img_rival = f'<img src="data:image/png;base64,{b64_rival}" style="height:90px;object-fit:contain;"/>' if b64_rival else f'<div class="team-name">{NAME_RIVAL}</div>'

    # Renderizado UI
    tab_equipo, tab_individual = st.tabs(["📊 Reporte de Equipo", "👤 Análisis Individual"])

    with tab_equipo:
        with st.container():
            st.markdown(f"""
            <div class="rugby-panel">
                <div class="hero">
                    <div style="font-size:3rem">🏆</div>
                    <div><div class="hero-title">Resumen de Partido</div><div class="hero-sub">{NAME_LOCAL} vs {NAME_RIVAL}</div></div>
                </div>
                <div class="scoreboard">
                    <div class="score-teams">
                        <div class="team-block">
                            {img_local}
                            <div class="team-name" style="margin-top:8px">{NAME_LOCAL}</div>
                            <div class="team-score">{s_l}</div>
                            <div class="score-detail">{t_l}T · {g_l}G · {p_l}P</div>
                        </div>
                        <div class="score-dash">vs</div>
                        <div class="team-block">
                            {img_rival}
                            <div class="team-name" style="margin-top:8px">{NAME_RIVAL}</div>
                            <div class="team-score">{s_r}</div>
                            <div class="score-detail">{t_r}T · {g_r}G · {p_r}P</div>
                        </div>
                    </div>
                    <div style="margin-top:25px; font-weight:900; font-size:1.5rem; letter-spacing:2px; text-align:center;">{res_txt}</div>
                </div>
                <div class="kpi-grid">
                    <div class="kpi-card"><div class="kpi-value">{total_tackles}</div><div class="kpi-label">Tackles</div><div class="kpi-sub">{pct_efectividad}% Éxito</div></div>
                    <div class="kpi-card"><div class="kpi-value">{total_penales}</div><div class="kpi-label">Penales</div><div class="kpi-sub">Cometidos</div></div>
                    <div class="kpi-card"><div class="kpi-value">{total_pescas}</div><div class="kpi-label">Pescas</div><div class="kpi-sub">Recuperos</div></div>
                    <div class="kpi-card"><div class="kpi-value">{total_enf}</div><div class="kpi-label">E. No Forzados</div><div class="kpi-sub">Pérdidas</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


        # ── LIDERES DEL PARTIDO ──
        mapa_dni = _cargar_mapa_dni_nombres()
        
        # ── CALCULOS PARA LIDERES NUEVOS ──
        # A) Apoyos, Primero y Segundo en el Ruck (desde 2 MOVILES)
        mov_rows = find_rows("MOVILES")
        apoyos_map = defaultdict(int)
        primero_map = defaultdict(int)
        segundo_map = defaultdict(int)
        
        for r in mov_rows:
            is_propio = get_int(r.get("propio"))
            team = r.get("team") or ""
            if is_propio or "CULP" in team.upper() or "UNI" in team.upper() or not team:
                raw_p = r.get("player") or r.get("jugador") or ""
                players = [clean_player(p.strip()) for p in raw_p.split("|") if p.strip()]
                if not players: continue
                
                # Apoyos
                for p in players:
                    apoyos_map[p] += 1
                    
                # Primero en el Ruck
                is_first = get_int(r.get("1"))
                if is_first:
                    primero_map[players[0]] += 1
                    
                # Segundo en el Ruck
                is_second = get_int(r.get("2"))
                if is_second:
                    p_seg = players[1] if len(players) > 1 else players[0]
                    segundo_map[p_seg] += 1
                    
        df_apoyos = pd.DataFrame([{"Jugador": k, "Apoyos": v} for k, v in apoyos_map.items()])
        if not df_apoyos.empty:
            df_apoyos = df_apoyos.sort_values("Apoyos", ascending=False)
            
        df_primero = pd.DataFrame([{"Jugador": k, "Primero": v} for k, v in primero_map.items()])
        if not df_primero.empty:
            df_primero = df_primero.sort_values("Primero", ascending=False)
            
        df_segundo = pd.DataFrame([{"Jugador": k, "Segundo": v} for k, v in segundo_map.items()])
        if not df_segundo.empty:
            df_segundo = df_segundo.sort_values("Segundo", ascending=False)

        # B) Puntos por Jugador (desde 12 PUNTOS (-))
        pts_all = find_rows("PUNTOS")
        pts_map = defaultdict(int)
        for r in pts_all:
            is_propio = get_int(r.get("propio"))
            is_rival = get_int(r.get("rival"))
            if is_rival and not is_propio:
                continue
            raw_p = r.get("player") or r.get("jugador") or ""
            p = clean_player(raw_p)
            if p:
                tries = get_int(r.get("try"))
                goals = get_int(r.get("goal"))
                penals = get_int(r.get("penal"))
                drops = get_int(r.get("drop"))
                try_penal = get_int(r.get("try penal"))
                pts = tries * 5 + goals * 2 + penals * 3 + drops * 3 + try_penal * 7
                pts_map[p] += pts
                
        df_puntos_jug = pd.DataFrame([{"Jugador": k, "Puntos": v} for k, v in pts_map.items()])
        if not df_puntos_jug.empty:
            df_puntos_jug = df_puntos_jug.sort_values("Puntos", ascending=False)

        # C) Pesca Ordenada por Recupera primero
        df_psc_sorted = pd.DataFrame()
        if not df_psc.empty:
            df_psc_sorted = df_psc.sort_values(by=["Recupera", "Total"], ascending=False)

        # ── RENDER DE LÍDERES ──
        st.markdown('<div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #fff;"><h2 style="color: #fff; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;">🏆 LÍDERES DEL PARTIDO</h2></div>', unsafe_allow_html=True)
        
        # Fila 1: 4 Columnas (Tackles, Quiebres, Apoyos, Puntos)
        lideres_cols_1 = st.columns(4)
        
        with lideres_cols_1[0]:
            if not df_tck.empty:
                lider = df_tck.iloc[0]
                st.markdown(_player_card_html(lider["Jugador"], "Tackles", lider["Total"], "#e3b341", mapa_dni), unsafe_allow_html=True)
                
        with lideres_cols_1[1]:
            if not df_qbr.empty:
                lider = df_qbr.iloc[0]
                st.markdown(_player_card_html(lider["Jugador"], "Quiebres", lider["Quiebres"], "#3fb950", mapa_dni), unsafe_allow_html=True)
                
        with lideres_cols_1[2]:
            if not df_apoyos.empty:
                lider = df_apoyos.iloc[0]
                st.markdown(_player_card_html(lider["Jugador"], "Apoyos (Ruck)", lider["Apoyos"], "#58a6ff", mapa_dni), unsafe_allow_html=True)
                
        with lideres_cols_1[3]:
            if not df_puntos_jug.empty:
                lider = df_puntos_jug.iloc[0]
                st.markdown(_player_card_html(lider["Jugador"], "Puntos Marcados", lider["Puntos"], "#a371f7", mapa_dni), unsafe_allow_html=True)
                
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        # Fila 2: 3 Columnas (Pesca, Primero Ruck, Segundo Ruck)
        lideres_cols_2 = st.columns(3)
        
        with lideres_cols_2[0]:
            if not df_psc_sorted.empty:
                lider = df_psc_sorted.iloc[0]
                st.markdown(_player_card_html(lider["Jugador"], "Pescas", lider["Recupera"], "#1f6feb", mapa_dni), unsafe_allow_html=True)
                
        with lideres_cols_2[1]:
            if not df_primero.empty:
                lider = df_primero.iloc[0]
                st.markdown(_player_card_html(lider["Jugador"], "Primero en Ruck", lider["Primero"], "#ff7b72", mapa_dni), unsafe_allow_html=True)
                
        with lideres_cols_2[2]:
            if not df_segundo.empty:
                lider = df_segundo.iloc[0]
                st.markdown(_player_card_html(lider["Jugador"], "Segundo en Ruck", lider["Segundo"], "#f2e05a", mapa_dni), unsafe_allow_html=True)
                
        st.markdown("<br>", unsafe_allow_html=True)
        
            # ── TACKLES ──
        st.markdown('<div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #e3b341;"><h2 style="color: #e3b341; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;">⚡ TACKLES POR JUGADOR</h2></div>', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 2])
        with col1:
            fig_tck = px.bar(df_tck.head(12), x="Total", y="Jugador", orientation="h", color="% Efectividad",
                             color_continuous_scale=["#f85149", "#e3b341", "#3fb950"], range_color=[40, 100],
                             labels={"Total": "N° Tackles", "Jugador": ""}, text="Total")
            fig_tck.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=600,
                                  margin=dict(l=220, r=40, t=10, b=10), yaxis=dict(autorange="reversed", tickfont=dict(family="Arial Black", size=18, color="#ffffff")), font=dict(family="Arial Black", size=18))
            st.plotly_chart(fig_tck, use_container_width=True, key="chart_tackles_bar")
        with col2:
            fig_donut = go.Figure(go.Pie(labels=["Efectivos", "Fallados"], values=[total_buenos, total_tackles-total_buenos],
                                         hole=0.65, marker_colors=["#3fb950", "#f85149"], textinfo="label+percent"))
            fig_donut.add_annotation(text=f"<span style='font-size:38px;font-weight:900;color:#3fb950'>{pct_efectividad}%</span><br><span style='font-size:12px;color:#8b949e;font-weight:bold'>EFECTIVIDAD</span>", font=dict(size=38, color="#3fb950", weight=900), showarrow=False)
            fig_donut.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=280,
                                    margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            st.plotly_chart(fig_donut, use_container_width=True, key="chart_tackles_donut")
            _df = df_tck[["Jugador","Total","Efectivos","Fallados","Dobles","% Efectividad"]].head(8)
            st.dataframe(
                _df.style
                    .set_properties(**{"background-color": "#161b22", "color": "#ffffff", "border-bottom": "1px solid #30363d", "font-size": "18px", "padding": "12px"})
                    .set_table_styles([{"selector": "th", "props": [("background-color", "#161b22"),
                                        ("color", "#58a6ff"), ("font-weight", "700"),
                                        ("font-size", "16px"), ("text-transform", "uppercase"),
                                        ("border-bottom", "2px solid #30363d")]}]),
                use_container_width=True, hide_index=True, key="df_tackles"
            )

        # ── QUIEBRES + SCRUMS ──
        df_qbr = df_qbr[~df_qbr["Jugador"].str.contains("Rival", case=False, na=False)]
        col_qbr, col_scr = st.columns([1, 1])
        with col_qbr:
            st.markdown('<div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #3fb950;"><h2 style="color: #3fb950; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;">💥 QUIEBRES DE LÍNEA</h2></div>', unsafe_allow_html=True)
            if not df_qbr.empty:
                fig_qbr = px.bar(df_qbr, x="Quiebres", y="Jugador", orientation="h", color="Quiebres",
                                 color_continuous_scale=["#1f6feb", "#58a6ff"], text="Quiebres")
                fig_qbr.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height= 450,
                                      margin=dict(l=220, r=20, t=10, b=10), showlegend=False, yaxis=dict(autorange="reversed", tickfont=dict(family="Arial Black", size=16, color="#ffffff")), font=dict(family="Arial Black", size=16))
                st.plotly_chart(fig_qbr, use_container_width=True, key="chart_quiebres")
            else:
                st.info("Sin datos de quiebres")
        with col_scr:
            st.markdown('<div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #58a6ff;"><h2 style="color: #58a6ff; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;">🏟️ SCRUMS</h2></div>', unsafe_allow_html=True)
            total_scrums = scrum_nuestros + scrum_rival
            if total_scrums > 0:
                fig_scr = go.Figure(go.Pie(
                    labels=[NAME_LOCAL, NAME_RIVAL],
                    values=[scrum_nuestros, scrum_rival],
                    hole=0.55,
                    marker_colors=["#58a6ff", "#f85149"],
                    textinfo="label+percent",
                    textfont=dict(family="Arial Black", size=14, color="white"),
                ))
                fig_scr.add_annotation(
                    text=f"<span style='font-size:38px;font-weight:900;color:#58a6ff'>{total_scrums}</span><br><span style='font-size:12px;color:#8b949e;font-weight:bold'>TOTAL SCRUMS</span>",
                    font=dict(size=22, color="#c9d1d9"),
                    showarrow=False
                )
                fig_scr.update_layout(
                    paper_bgcolor="#161b22", plot_bgcolor="#161b22",
                    font_color="#c9d1d9", height= 450,
                    margin=dict(l=0, r=0, t=10, b=0),
                    showlegend=False,
                    legend=dict(orientation="h", y=-0.1, font=dict(color="#8b949e"))
                )
                st.plotly_chart(fig_scr, use_container_width=True, key="chart_scrums")
            else:
                st.info("Sin datos de scrums")

        # ── KICKS ──
        st.markdown('<div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #a371f7;"><h2 style="color: #a371f7; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;">🦵 ANÁLISIS DE KICKS (PATADAS)</h2></div>', unsafe_allow_html=True)
        
        kicks_total_team = len(kck_rows)
        kicks_gana_team = team_kicks_stats["gana"]
        kicks_pct_efectiva = round(kicks_gana_team / kicks_total_team * 100) if kicks_total_team else 0
        kicks_recup_team = team_kicks_stats["recupero"]
        kicks_errors_team = (team_kicks_stats["pelota_tapada"] + 
                             team_kicks_stats["directo_touch"] + 
                             team_kicks_stats["directo_ingoal"] + 
                             team_kicks_stats["palos_errados"] + 
                             team_kicks_stats["mala_ejecucion"] + 
                             team_kicks_stats["penal_touch"])
        
        st.markdown(f"""
        <div class="kpi-grid" style="margin-bottom: 25px;">
            <div class="kpi-card">
                <div class="kpi-value" style="color:#a371f7">{kicks_total_team}</div>
                <div class="kpi-label">Kicks Totales</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:#3fb950">{kicks_pct_efectiva}%</div>
                <div class="kpi-label">Efectividad (% Gana Terreno)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:#58a6ff">{kicks_recup_team}</div>
                <div class="kpi-label">Posesiones Recuperadas</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:#f85149">{kicks_errors_team}</div>
                <div class="kpi-label">Kicks Fallidos / Errores</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_kck1, col_kck2 = st.columns([1, 1])
        with col_kck1:
            st.markdown('<h3 style="color: #a371f7; font-size: 20px; font-weight: 700; margin-bottom: 10px;">📊 TIPOS DE KICKS POR JUGADOR</h3>', unsafe_allow_html=True)
            if not df_kck.empty:
                fig_types = px.bar(df_kck, x="Jugador", y=["Territorial", "Bajo Presión", "A Disputar / Cajón", "Otros Tipos"],
                                   barmode="stack", color_discrete_sequence=["#1f6feb", "#58a6ff", "#3fb950", "#e3b341"])
                fig_types.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=400,
                                        margin=dict(l=40, r=20, t=10, b=140), legend=dict(orientation="h", y=1.15, font=dict(size=12)), xaxis=dict(tickfont=dict(family="Arial Black", size=15, color="#ffffff")), font=dict(family="Arial Black", size=14))
                st.plotly_chart(fig_types, use_container_width=True, key="chart_kicks_types")
            else:
                st.info("Sin datos de kicks")
                
        with col_kck2:
            st.markdown('<h3 style="color: #a371f7; font-size: 20px; font-weight: 700; margin-bottom: 10px;">🎯 DISTRIBUCIÓN DE KICKS DEL EQUIPO</h3>', unsafe_allow_html=True)
            t_types_vals = [
                team_kicks_stats["territorial"],
                team_kicks_stats["bajo_presion"],
                team_kicks_stats["a_disputar"],
                (team_kicks_stats["rastron"] + team_kicks_stats["sombrero"] + team_kicks_stats["pase"] + team_kicks_stats["50_22"])
            ]
            t_types_labels = ["Territorial", "Bajo Presión", "A Disputar / Cajón", "Otros Kicks"]
            
            if sum(t_types_vals) > 0:
                fig_donut_kck = go.Figure(go.Pie(
                    labels=t_types_labels,
                    values=t_types_vals,
                    hole=0.6,
                    marker_colors=["#1f6feb", "#58a6ff", "#3fb950", "#e3b341"],
                    textinfo="label+percent",
                    textfont=dict(family="Arial Black", size=12, color="white")
                ))
                fig_donut_kck.add_annotation(
                    text=f"<span style='font-size:32px;font-weight:900;color:#a371f7'>{kicks_total_team}</span><br><span style='font-size:10px;color:#8b949e;font-weight:bold'>TOTAL KICKS</span>",
                    showarrow=False
                )
                fig_donut_kck.update_layout(
                    paper_bgcolor="#161b22", plot_bgcolor="#161b22",
                    font_color="#c9d1d9", height=400,
                    margin=dict(l=0, r=0, t=10, b=0),
                    showlegend=False
                )
                st.plotly_chart(fig_donut_kck, use_container_width=True, key="chart_kicks_donut")
            else:
                st.info("Sin datos de tipos de kicks")
                
        st.markdown('<h3 style="color: #a371f7; font-size: 20px; font-weight: 700; margin-top: 20px; margin-bottom: 10px;">📋 DETALLE DE KICKS POR JUGADOR</h3>', unsafe_allow_html=True)
        if not df_kck.empty:
            st.dataframe(
                df_kck.style
                    .set_properties(**{"background-color": "#161b22", "color": "#ffffff", "border-bottom": "1px solid #30363d", "font-size": "18px", "padding": "12px"})
                    .set_table_styles([{"selector": "th", "props": [("background-color", "#161b22"),
                                        ("color", "#a371f7"), ("font-weight", "700"),
                                        ("font-size", "16px"), ("text-transform", "uppercase"),
                                        ("border-bottom", "2px solid #30363d")]}]),
                use_container_width=True, hide_index=True, key="df_kicks_detailed"
            )

        # ── PESCA ──
        st.markdown('<div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #1f6feb;"><h2 style="color: #1f6feb; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;">🎣 PESCA (RESTART CONTEST)</h2></div>', unsafe_allow_html=True)
        col7, col8, col9 = st.columns([1, 2, 2])
        with col7:
            st.markdown(f"""
            <div class="kpi-grid" style="flex-direction:column; gap:12px">
                <div class="kpi-card"><div class="kpi-value">{pesca_nosotros}</div><div class="kpi-label">Pesquemos</div><div class="kpi-sub">{pesca_recupera} recuperadas</div></div>
                <div class="kpi-card"><div class="kpi-value" style="color:#f85149">{pesca_rival}</div><div class="kpi-label">Pesca Rival</div></div>
                <div class="kpi-card"><div class="kpi-value" style="color:#e3b341">{pesca_penal_u}</div><div class="kpi-label">Penales a favor</div></div>
            </div>
            """, unsafe_allow_html=True)
        with col8:
            if not df_psc.empty:
                fig_psc = px.bar(df_psc, x="Total", y="Jugador", orientation="h", color="Recupera",
                                 color_continuous_scale=["#1f6feb", "#3fb950"], text="Total")
                fig_psc.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height= 350,
                                      margin=dict(l=220, r=20, t=10, b=10), yaxis=dict(autorange="reversed", tickfont=dict(family="Arial Black", size=16, color="#ffffff")), font=dict(family="Arial Black", size=16))
                st.plotly_chart(fig_psc, use_container_width=True, key="chart_pesca")
        with col9:
            st.dataframe(
                df_psc.style
                    .set_properties(**{"background-color": "#161b22", "color": "#ffffff", "border-bottom": "1px solid #30363d", "font-size": "18px", "padding": "12px"})
                    .set_table_styles([{"selector": "th", "props": [("background-color", "#161b22"),
                                        ("color", "#58a6ff"), ("font-weight", "700"),
                                        ("font-size", "16px"), ("text-transform", "uppercase"),
                                        ("border-bottom", "2px solid #30363d")]}]),
                use_container_width=True, hide_index=True, key="df_pesca"
            )

        # ── PENALES ──
        st.markdown('<div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #e3b341;"><h2 style="color: #e3b341; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;">🟡 PENALES Y FREE KICKS</h2></div>', unsafe_allow_html=True)
        c10, c11 = st.columns([2, 3])
        with c10:
            fig_pnl_donut = go.Figure(go.Pie(labels=["A favor", "En contra"], values=[pnl_u, pnl_rival], hole=0.6,
                                             marker_colors=["#3fb950", "#f85149"], textinfo="label+value"))
            fig_pnl_donut.add_annotation(text=f"<span style=\'font-size:38px;font-weight:900;color:#e3b341\'>{pnl_total}</span><br><span style=\'font-size:12px;color:#8b949e;font-weight:bold\'>TOTAL</span>", showarrow=False)
            fig_pnl_donut.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height= 350, font=dict(family="Arial Black", size=14), margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_pnl_donut, use_container_width=True, key="chart_penales_donut")
        with c11:
            if not df_pnl_jug.empty:
                fig_pnl_jug = px.bar(df_pnl_jug, x="Penales Cometidos", y="Jugador", orientation="h", text="Penales Cometidos", color_discrete_sequence=["#e3b341"])
                fig_pnl_jug.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height= 350, font=dict(family="Arial Black", size=16), margin=dict(l=220, r=20, t=10, b=10), yaxis=dict(autorange="reversed", tickfont=dict(family="Arial Black", size=16, color="#ffffff")))
                st.plotly_chart(fig_pnl_jug, use_container_width=True, key="chart_penales_jug")

        # ── LINE OUT ──
        st.markdown('<div class="section-header">📏 Line Out</div>', unsafe_allow_html=True)

        # KPIs superiores
        pct_limpia_prop = round(lin_limpia / lin_total_prop * 100) if lin_total_prop else 0
        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-value" style="color:#58a6ff">{lin_total}</div>
                <div class="kpi-label">Total Lines</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:#3fb950">{lin_total_prop}</div>
                <div class="kpi-label">Lines Propios</div>
                <div class="kpi-sub">{NAME_LOCAL}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:#f85149">{lin_total_riv}</div>
                <div class="kpi-label">Lines Rivales</div>
                <div class="kpi-sub">{NAME_RIVAL}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:#3fb950">{lin_limpia}</div>
                <div class="kpi-label">Pelota Limpia</div>
                <div class="kpi-sub">{pct_limpia_prop}% de los propios</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:#f85149">{lin_robada}</div>
                <div class="kpi-label">Robadas</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:#e3b341">{lin_perdida}</div>
                <div class="kpi-label">Perdidas</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Desglose completo nuestros lines
        lin_col1, lin_col2 = st.columns(2)
        with lin_col1:
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:18px">
                <div style="font-size:0.85rem;color:#58a6ff;font-weight:700;margin-bottom:12px;text-transform:uppercase">
                    🔵 Nuestros Lines — Resultados ({lin_total_prop} totales)
                </div>
                <table style="width:100%;border-collapse:collapse;color:#c9d1d9;font-size:0.9rem">
                  <tr><td style="padding:5px 0">✅ Pelota Limpia</td>  <td style="text-align:right;font-weight:700;color:#3fb950">{lin_limpia}</td></tr>
                  <tr><td style="padding:5px 0">🛑 Pelota Sucia</td>   <td style="text-align:right;font-weight:700;color:#e3b341">{lin_sucia}</td></tr>
                  <tr><td style="padding:5px 0">❌ Robada</td>          <td style="text-align:right;font-weight:700;color:#f85149">{lin_robada}</td></tr>
                  <tr><td style="padding:5px 0">❌ Perdida</td>         <td style="text-align:right;font-weight:700;color:#f85149">{lin_perdida}</td></tr>
                  <tr><td style="padding:5px 0">↪️ Torcida</td>         <td style="text-align:right;font-weight:700;color:#8b949e">{lin_torcida}</td></tr>
                  <tr><td style="padding:5px 0">➡️ Pasada</td>          <td style="text-align:right;font-weight:700;color:#8b949e">{lin_pasada}</td></tr>
                  <tr><td style="padding:5px 0">⚡ Tiro Rápido</td>      <td style="text-align:right;font-weight:700;color:#a371f7">{lin_rapido}</td></tr>
                  <tr><td style="padding:5px 0">🟢 Infracción para U</td><td style="text-align:right;font-weight:700;color:#3fb950">{lin_inf_u}</td></tr>
                  <tr><td style="padding:5px 0">🔴 Infracción Rival</td> <td style="text-align:right;font-weight:700;color:#f85149">{lin_inf_riv}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        with lin_col2:
            # Grafico de posicion del lanzamiento
            results_data = {
                "Resultado": ["Limpia", "Sucia", "Robada", "Perdida", "Torcida", "Pasada", "T. Rápido"],
                "N°":        [lin_limpia, lin_sucia, lin_robada, lin_perdida, lin_torcida, lin_pasada, lin_rapido]
            }
            df_lin_res = pd.DataFrame(results_data)
            df_lin_res = df_lin_res[df_lin_res["N°"] > 0]
            if not df_lin_res.empty:
                color_map = {"Limpia": "#3fb950", "Sucia": "#e3b341", "Robada": "#f85149",
                             "Perdida": "#f85149", "Torcida": "#8b949e", "Pasada": "#58a6ff", "T. Rápido": "#a371f7"}
                fig_lin = px.bar(df_lin_res, x="Resultado", y="N°", text="N°",
                                 color="Resultado", color_discrete_map=color_map)
                fig_lin.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22",
                                      font_color="#c9d1d9", height=280, showlegend=False,
                                      margin=dict(l=0, r=0, t=10, b=10),
                                      yaxis=dict(gridcolor="#21262d"))
                fig_lin.update_traces(textfont_color="#fff", textposition="outside")
                st.plotly_chart(fig_lin, use_container_width=True, key="chart_lineout")
            # Posicion de lanzamiento
            if lin_2m + lin_4m + lin_6m > 0:
                st.markdown(f"""
                <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px;margin-top:10px">
                    <div style="font-size:0.8rem;color:#8b949e;font-weight:700;margin-bottom:8px;text-transform:uppercase">Posición de lanzamiento</div>
                    <div style="display:flex;gap:16px;justify-content:center">
                        <div style="text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#58a6ff">{lin_2m}</div><div style="font-size:0.75rem;color:#8b949e">2 hombre</div></div>
                        <div style="text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#58a6ff">{lin_4m}</div><div style="font-size:0.75rem;color:#8b949e">4 hombre</div></div>
                        <div style="text-align:center"><div style="font-size:1.6rem;font-weight:900;color:#58a6ff">{lin_6m}</div><div style="font-size:0.75rem;color:#8b949e">6 hombre</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("""<div style="text-align:center; color:#484f58; font-size:0.8rem; margin-top:50px; padding:20px; border-top:1px solid #21262d">Club Universitario de La Plata · Sistema de Rendimiento</div>""", unsafe_allow_html=True)

        # ── BOTÓN EXPORTAR PDF ──
        st.markdown("---")

        # Guardamos el PDF en session_state para que sobreviva al rerun de Streamlit
        pdf_key = f"pdf_bytes_{selected_match}"

        col_pdf_l, col_pdf_c, col_pdf_r = st.columns([2, 1, 2])
        with col_pdf_c:
            if st.button("📄 Generar PDF", use_container_width=True, type="primary", key="btn_gen_pdf"):
                with st.spinner("Generando informe PDF..."):
                    st.session_state[pdf_key] = _generar_pdf(
                        selected_match=selected_match,
                        name_local=NAME_LOCAL, name_rival=NAME_RIVAL,
                        s_l=s_l, s_r=s_r, t_l=t_l, g_l=g_l, p_l=p_l,
                        t_r=t_r, g_r=g_r, p_r=p_r, res_txt=res_txt,
                        total_tackles=total_tackles, total_buenos=total_buenos,
                        pct_efectividad=pct_efectividad, df_tck=df_tck,
                        df_qbr=df_qbr,
                        scrum_nuestros=scrum_nuestros, scrum_rival=scrum_rival,
                        df_kck=df_kck,
                        pesca_nosotros=pesca_nosotros, pesca_recupera=pesca_recupera,
                        pesca_rival=pesca_rival,
                        pnl_u=pnl_u, pnl_rival=pnl_rival, df_causas=df_causas,
                        lin_total=lin_total, lin_total_prop=lin_total_prop,
                        lin_total_riv=lin_total_riv, lin_limpia=lin_limpia,
                        lin_robada=lin_robada, lin_perdida=lin_perdida,
                        lin_sucia=lin_sucia, lin_torcida=lin_torcida,
                        lin_rapido=lin_rapido,
                    )

        # El download_button se muestra siempre que haya bytes en session_state
        # (sobrevive al rerun que dispara Streamlit al hacer clic)
        if st.session_state.get(pdf_key):
            col_dl_l, col_dl_c, col_dl_r = st.columns([2, 1, 2])
            with col_dl_c:
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=st.session_state[pdf_key],
                    file_name=f"informe_{selected_match.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_dl_pdf",
                )

    with tab_individual:
        # Obtener jugadores participantes en el partido actual
        participantes = set()
        if not df_tck.empty and 'Jugador' in df_tck.columns:
            participantes.update(df_tck['Jugador'].dropna().unique())
        if not df_qbr.empty and 'Jugador' in df_qbr.columns:
            participantes.update(df_qbr['Jugador'].dropna().unique())
        if not df_apoyos.empty and 'Jugador' in df_apoyos.columns:
            participantes.update(df_apoyos['Jugador'].dropna().unique())
        if not df_puntos_jug.empty and 'Jugador' in df_puntos_jug.columns:
            participantes.update(df_puntos_jug['Jugador'].dropna().unique())
        if not df_kck.empty and 'Jugador' in df_kck.columns:
            participantes.update(df_kck['Jugador'].dropna().unique())
        if not df_psc.empty and 'Jugador' in df_psc.columns:
            participantes.update(df_psc['Jugador'].dropna().unique())
        if not df_pnl_jug.empty and 'Jugador' in df_pnl_jug.columns:
            participantes.update(df_pnl_jug['Jugador'].dropna().unique())
            
        participantes_lista = sorted(list(participantes))
        
        if not participantes_lista:
            st.info("ℹ️ No se encontraron registros individuales de jugadores para este partido.")
        else:
            col_sel_p, _ = st.columns([2, 2])
            with col_sel_p:
                jugador_sel = st.selectbox("Seleccionar Jugador para Análisis", participantes_lista, key="sb_jugador_sel")
            
            # Cargar mapas y obtener detalles
            mapa_dni = _cargar_mapa_dni_nombres()
            detalles_map = _cargar_detalles_jugadores()
            
            # Buscar DNI
            dni = _buscar_dni_por_nombre(jugador_sel, mapa_dni)
            p_details = detalles_map.get(dni, {
                "nombre": jugador_sel,
                "posicion": "N/A",
                "categoria": "N/A",
                "dni": dni or "N/A"
            })
            
            # Obtener foto en base64
            foto_b64 = _get_foto_b64(jugador_sel, mapa_dni)
            avatar_html = f'<img src="data:image/jpeg;base64,{foto_b64}" style="width:120px;height:120px;border-radius:15px;object-fit:cover;border:3px solid #ffffff;box-shadow:0 4px 12px rgba(0,0,0,0.5);"/>' if foto_b64 else f'<div style="width:120px;height:120px;border-radius:15px;background:#1c2030;border:3px solid #ffffff;display:flex;align-items:center;justify-content:center;font-size:48px;color:#8b949e;box-shadow:0 4px 12px rgba(0,0,0,0.5)">👤</div>'
            
            # Tarjeta de Perfil Estilo Universitario
            st.markdown(f"""
            <div style="background:#161b22; border:1px solid #30363d; border-radius:16px; padding:20px; margin-top: 15px; margin-bottom:25px; box-shadow:0 8px 24px rgba(0,0,0,0.3); border-left:6px solid #ffffff;">
                <div style="display:flex; flex-wrap:wrap; align-items:center; gap:20px;">
                    <div>{avatar_html}</div>
                    <div style="flex-grow:1;">
                        <h2 style="margin:0; font-size:1.8rem; font-weight:900; color:#ffffff; text-transform:uppercase; letter-spacing:1px;">{p_details['nombre']}</h2>
                        <div style="display:flex; flex-wrap:wrap; gap:12px; margin-top:10px;">
                            <span style="background:#21262d; border:1px solid #30363d; color:#c9d1d9; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight:600;">📋 DNI: {p_details['dni']}</span>
                            <span style="background:#21262d; border:1px solid #30363d; color:#c9d1d9; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight:600;">🏉 Puesto: {p_details['posicion']}</span>
                            <span style="background:#21262d; border:1px solid #30363d; color:#c9d1d9; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight:600;">🏷️ Categoría: {p_details['categoria']}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Calcular estadísticas en este partido para el jugador seleccionado
            # A. Tackles
            p_tck = df_tck[df_tck['Jugador'] == jugador_sel].iloc[0] if not df_tck.empty and jugador_sel in df_tck['Jugador'].values else None
            t_total = int(p_tck['Total']) if p_tck is not None else 0
            t_ok = int(p_tck['Efectivos']) if p_tck is not None else 0
            t_fail = int(p_tck['Fallados']) if p_tck is not None else 0
            t_doble = int(p_tck['Dobles']) if p_tck is not None else 0
            t_pct = int(p_tck['% Efectividad']) if p_tck is not None else 0
            
            # B. Quiebres
            p_qbr = df_qbr[df_qbr['Jugador'] == jugador_sel].iloc[0] if not df_qbr.empty and jugador_sel in df_qbr['Jugador'].values else None
            qbr_val = int(p_qbr['Quiebres']) if p_qbr is not None else 0
            
            # C. Apoyos / Rucks
            p_apoyo = df_apoyos[df_apoyos['Jugador'] == jugador_sel].iloc[0] if not df_apoyos.empty and jugador_sel in df_apoyos['Jugador'].values else None
            ap_val = int(p_apoyo['Apoyos']) if p_apoyo is not None else 0
            
            p_prim = df_primero[df_primero['Jugador'] == jugador_sel].iloc[0] if not df_primero.empty and jugador_sel in df_primero['Jugador'].values else None
            prim_val = int(p_prim['Primero']) if p_prim is not None else 0
            
            p_seg = df_segundo[df_segundo['Jugador'] == jugador_sel].iloc[0] if not df_segundo.empty and jugador_sel in df_segundo['Jugador'].values else None
            seg_val = int(p_seg['Segundo']) if p_seg is not None else 0
            
            # D. Puntos
            p_pts = df_puntos_jug[df_puntos_jug['Jugador'] == jugador_sel].iloc[0] if not df_puntos_jug.empty and jugador_sel in df_puntos_jug['Jugador'].values else None
            pts_val = int(p_pts['Puntos']) if p_pts is not None else 0
            
            pts_jugador_rows = [r for r in find_rows("PUNTOS") if _clean_player(r.get("player") or r.get("jugador")) == jugador_sel]
            tries_val = sum(get_int(r.get("try")) for r in pts_jugador_rows)
            
            # E. Kicks
            p_kck = df_kck[df_kck['Jugador'] == jugador_sel].iloc[0] if not df_kck.empty and jugador_sel in df_kck['Jugador'].values else None
            kck_total = int(p_kck['Total Kicks']) if p_kck is not None else 0
            kck_gana = int(p_kck['Gana Terreno']) if p_kck is not None else 0
            kck_err = int(p_kck['Errores']) if p_kck is not None else 0
            kck_pct = int(p_kck['% Efectividad']) if p_kck is not None else 0
            
            # F. Pesca
            p_psc = df_psc[df_psc['Jugador'] == jugador_sel].iloc[0] if not df_psc.empty and jugador_sel in df_psc['Jugador'].values else None
            psc_total = int(p_psc['Total']) if p_psc is not None else 0
            psc_rec = int(p_psc['Recupera']) if p_psc is not None else 0
            
            # G. Penales Cometidos
            p_pnl = df_pnl_jug[df_pnl_jug['Jugador'] == jugador_sel].iloc[0] if not df_pnl_jug.empty and jugador_sel in df_pnl_jug['Jugador'].values else None
            pnl_val = int(p_pnl['Penales Cometidos']) if p_pnl is not None else 0
            
            st.markdown('<h3 style="color: #ffffff; font-size: 20px; font-weight: 800; margin-bottom: 15px; border-bottom: 2px solid #222; padding-bottom: 8px;">📊 RENDIMIENTO EN ESTE PARTIDO</h3>', unsafe_allow_html=True)
            
            kpi_cols = st.columns(4)
            with kpi_cols[0]:
                st.markdown(f"""
                <div style="background:#161b22; border:1px solid #30363d; border-radius:12px; padding:15px; text-align:center; min-height:120px;">
                    <div style="font-size:2rem; font-weight:900; color:#e3b341;">{t_total}</div>
                    <div style="font-size:0.75rem; color:#8b949e; font-weight:700; text-transform:uppercase;">Tackles Realizados</div>
                    <div style="font-size:0.8rem; color:#3fb950; font-weight:bold; margin-top:5px;">{t_pct}% Éxito</div>
                </div>
                """, unsafe_allow_html=True)
            with kpi_cols[1]:
                st.markdown(f"""
                <div style="background:#161b22; border:1px solid #30363d; border-radius:12px; padding:15px; text-align:center; min-height:120px;">
                    <div style="font-size:2rem; font-weight:900; color:#58a6ff;">{ap_val}</div>
                    <div style="font-size:0.75rem; color:#8b949e; font-weight:700; text-transform:uppercase;">Apoyos en Ruck</div>
                    <div style="font-size:0.8rem; color:#8b949e; margin-top:5px;">1°: {prim_val} | 2°: {seg_val}</div>
                </div>
                """, unsafe_allow_html=True)
            with kpi_cols[2]:
                st.markdown(f"""
                <div style="background:#161b22; border:1px solid #30363d; border-radius:12px; padding:15px; text-align:center; min-height:120px;">
                    <div style="font-size:2rem; font-weight:900; color:#3fb950;">{qbr_val}</div>
                    <div style="font-size:0.75rem; color:#8b949e; font-weight:700; text-transform:uppercase;">Quiebres de Línea</div>
                    <div style="font-size:0.8rem; color:#a371f7; font-weight:bold; margin-top:5px;">{pts_val} Pts ({tries_val} Tries)</div>
                </div>
                """, unsafe_allow_html=True)
            with kpi_cols[3]:
                st.markdown(f"""
                <div style="background:#161b22; border:1px solid #30363d; border-radius:12px; padding:15px; text-align:center; min-height:120px;">
                    <div style="font-size:2rem; font-weight:900; color:#f85149;">{pnl_val}</div>
                    <div style="font-size:0.75rem; color:#8b949e; font-weight:700; text-transform:uppercase;">Penales Cometidos</div>
                    <div style="font-size:0.8rem; color:#1f6feb; font-weight:bold; margin-top:5px;">Pescas: {psc_rec}/{psc_total}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Comparar con promedios del equipo
            avg_tackles = df_tck['Total'].mean() if not df_tck.empty else 0
            avg_apoyos = df_apoyos['Apoyos'].mean() if not df_apoyos.empty else 0
            avg_quiebres = df_qbr['Quiebres'].mean() if not df_qbr.empty else 0
            avg_puntos = df_puntos_jug['Puntos'].mean() if not df_puntos_jug.empty else 0
            avg_pescas = df_psc['Total'].mean() if not df_psc.empty else 0
            avg_penales = df_pnl_jug['Penales Cometidos'].mean() if not df_pnl_jug.empty else 0
            
            comp_data = pd.DataFrame([
                {"Métrica": "Tackles", "Jugador": t_total, "Promedio Equipo": round(avg_tackles, 1)},
                {"Métrica": "Apoyos Ruck", "Jugador": ap_val, "Promedio Equipo": round(avg_apoyos, 1)},
                {"Métrica": "Quiebres", "Jugador": qbr_val, "Promedio Equipo": round(avg_quiebres, 1)},
                {"Métrica": "Puntos", "Jugador": pts_val, "Promedio Equipo": round(avg_puntos, 1)},
                {"Métrica": "Pescas", "Jugador": psc_total, "Promedio Equipo": round(avg_pescas, 1)},
                {"Métrica": "Penales", "Jugador": pnl_val, "Promedio Equipo": round(avg_penales, 1)}
            ])
            
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=comp_data["Métrica"],
                y=comp_data["Jugador"],
                name=jugador_sel,
                marker_color="#ffffff",
                text=comp_data["Jugador"],
                textposition="auto"
            ))
            fig_comp.add_trace(go.Bar(
                x=comp_data["Métrica"],
                y=comp_data["Promedio Equipo"],
                name="Promedio Equipo",
                marker_color="#444444",
                text=comp_data["Promedio Equipo"],
                textposition="auto"
            ))
            
            fig_comp.update_layout(
                barmode='group',
                paper_bgcolor="#161b22",
                plot_bgcolor="#161b22",
                font_color="#c9d1d9",
                height=350,
                margin=dict(l=40, r=40, t=30, b=30),
                legend=dict(orientation="h", y=1.1, font=dict(color="#8b949e")),
                yaxis=dict(gridcolor="#21262d", title="Cantidad")
            )
            
            st.markdown('<br>', unsafe_allow_html=True)
            col_chart_comp, col_table_comp = st.columns([3, 2])
            with col_chart_comp:
                st.markdown('<h4 style="color: #ffffff; font-size: 16px; font-weight: 700; margin-bottom: 10px;">📊 COMPARATIVA CON EL EQUIPO</h4>', unsafe_allow_html=True)
                st.plotly_chart(fig_comp, use_container_width=True, key="chart_indiv_comp")
                
            with col_table_comp:
                st.markdown('<h4 style="color: #ffffff; font-size: 16px; font-weight: 700; margin-bottom: 10px;">📋 DETALLE DE METRICAS DEL PARTIDO</h4>', unsafe_allow_html=True)
                
                tck_details_txt = f"{t_ok} de {t_total} ({t_pct}% éxito) · {t_doble} dobles"
                kck_details_txt = f"{kck_total} ({kck_gana} gana terr., {kck_err} err.)" if kck_total else "Sin kicks"
                psc_details_txt = f"{psc_rec} recuperadas de {psc_total} intentos" if psc_total else "Sin intentos de pesca"
                ruck_details_txt = f"{ap_val} rucks (1° arribo: {prim_val}, 2° arribo: {seg_val})"
                
                st.markdown(f"""
                <div style="background:#161b22; border:1px solid #30363d; border-radius:12px; padding:15px; height:100%; color:#c9d1d9; font-size:0.9rem;">
                    <div style="border-bottom:1px solid #21262d; padding:8px 0; display:flex; justify-content:space-between; gap:10px;">
                        <span style="font-weight:600;">Desempeño de Tackle:</span>
                        <span style="color:#ffffff; font-weight:700; text-align:right;">{tck_details_txt}</span>
                    </div>
                    <div style="border-bottom:1px solid #21262d; padding:8px 0; display:flex; justify-content:space-between; gap:10px;">
                        <span style="font-weight:600;">Participación en Rucks:</span>
                        <span style="color:#ffffff; font-weight:700; text-align:right;">{ruck_details_txt}</span>
                    </div>
                    <div style="border-bottom:1px solid #21262d; padding:8px 0; display:flex; justify-content:space-between; gap:10px;">
                        <span style="font-weight:600;">Juego con el pie (Kicks):</span>
                        <span style="color:#ffffff; font-weight:700; text-align:right;">{kck_details_txt}</span>
                    </div>
                    <div style="border-bottom:1px solid #21262d; padding:8px 0; display:flex; justify-content:space-between; gap:10px;">
                        <span style="font-weight:600;">Restart Contest (Pescas):</span>
                        <span style="color:#ffffff; font-weight:700; text-align:right;">{psc_details_txt}</span>
                    </div>
                    <div style="padding:8px 0; display:flex; justify-content:space-between; gap:10px;">
                        <span style="font-weight:600;">Puntos anotados:</span>
                        <span style="color:#3fb950; font-weight:700; text-align:right;">{pts_val} pts ({tries_val} tries)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # Historial y tendencias
            st.markdown('<br><h3 style="color: #ffffff; font-size: 20px; font-weight: 800; margin-bottom: 15px; border-bottom: 2px solid #222; padding-bottom: 8px;">📈 HISTORIAL Y TENDENCIAS EN EL TORNEO</h3>', unsafe_allow_html=True)
            
            with st.spinner("Cargando historial del jugador..."):
                matches_tuple = tuple(matches)
                mapa_dni_tuple = tuple(sorted(mapa_dni.items()))
                df_hist = _get_player_historical_stats(jugador_sel, matches_tuple, mapa_dni_tuple)
                
            if df_hist.empty:
                st.info("ℹ️ No hay suficiente historial para este jugador en otros partidos.")
            else:
                partidos_jugados = len(df_hist)
                tot_puntos = df_hist['Puntos'].sum()
                tot_tries = df_hist['Tries'].sum()
                tot_tackles = df_hist['Tackles'].sum()
                tot_tackles_ok = df_hist['Tackles Efectivos'].sum()
                tot_apoyos = df_hist['Apoyos Ruck'].sum()
                tot_penales = df_hist['Penales Cometidos'].sum()
                pct_tackles_carrera = round(tot_tackles_ok / tot_tackles * 100) if tot_tackles else 0
                
                carr_cols = st.columns(5)
                with carr_cols[0]:
                    st.markdown(f"""
                    <div style="background:#161b22; border:1px solid #30363d; border-radius:10px; padding:10px; text-align:center;">
                        <div style="font-size:1.5rem; font-weight:900; color:#58a6ff;">{partidos_jugados}</div>
                        <div style="font-size:0.7rem; color:#8b949e; font-weight:700; text-transform:uppercase;">Partidos</div>
                    </div>
                    """, unsafe_allow_html=True)
                with carr_cols[1]:
                    st.markdown(f"""
                    <div style="background:#161b22; border:1px solid #30363d; border-radius:10px; padding:10px; text-align:center;">
                        <div style="font-size:1.5rem; font-weight:900; color:#e3b341;">{tot_tackles}</div>
                        <div style="font-size:0.7rem; color:#8b949e; font-weight:700; text-transform:uppercase;">Tackles ({pct_tackles_carrera}%)</div>
                    </div>
                    """, unsafe_allow_html=True)
                with carr_cols[2]:
                    st.markdown(f"""
                    <div style="background:#161b22; border:1px solid #30363d; border-radius:10px; padding:10px; text-align:center;">
                        <div style="font-size:1.5rem; font-weight:900; color:#3fb950;">{tot_tries}</div>
                        <div style="font-size:0.7rem; color:#8b949e; font-weight:700; text-transform:uppercase;">Tries ({tot_puntos} Pts)</div>
                    </div>
                    """, unsafe_allow_html=True)
                with carr_cols[3]:
                    st.markdown(f"""
                    <div style="background:#161b22; border:1px solid #30363d; border-radius:10px; padding:10px; text-align:center;">
                        <div style="font-size:1.5rem; font-weight:900; color:#a371f7;">{tot_apoyos}</div>
                        <div style="font-size:0.7rem; color:#8b949e; font-weight:700; text-transform:uppercase;">Apoyos Ruck</div>
                    </div>
                    """, unsafe_allow_html=True)
                with carr_cols[4]:
                    st.markdown(f"""
                    <div style="background:#161b22; border:1px solid #30363d; border-radius:10px; padding:10px; text-align:center;">
                        <div style="font-size:1.5rem; font-weight:900; color:#f85149;">{tot_penales}</div>
                        <div style="font-size:0.7rem; color:#8b949e; font-weight:700; text-transform:uppercase;">Penales Com.</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('<br>', unsafe_allow_html=True)
                col_trend1, col_trend2 = st.columns(2)
                
                with col_trend1:
                    st.markdown('<h4 style="color: #ffffff; font-size: 15px; font-weight: 700; margin-bottom: 10px;">📉 EVOLUCIÓN DE TACKLES (CANTIDAD Y EFECTIVIDAD)</h4>', unsafe_allow_html=True)
                    fig_trend_tck = make_subplots(specs=[[{"secondary_y": True}]])
                    fig_trend_tck.add_trace(
                        go.Scatter(x=df_hist["Partido"], y=df_hist["Tackles"], name="Tackles Totales", marker_color="#ffffff", line=dict(width=3)),
                        secondary_y=False,
                    )
                    fig_trend_tck.add_trace(
                        go.Scatter(x=df_hist["Partido"], y=df_hist["% Tackles"], name="% Efectividad", marker_color="#e3b341", line=dict(dash="dash", width=3)),
                        secondary_y=True,
                    )
                    fig_trend_tck.update_layout(
                        paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9",
                        height=300, margin=dict(l=40, r=40, t=10, b=10),
                        legend=dict(orientation="h", y=1.2, font=dict(color="#8b949e")),
                    )
                    fig_trend_tck.update_xaxes(gridcolor="#21262d")
                    fig_trend_tck.update_yaxes(title_text="N° Tackles", secondary_y=False, gridcolor="#21262d")
                    fig_trend_tck.update_yaxes(title_text="% Efectividad", secondary_y=True, range=[0, 105], showgrid=False)
                    st.plotly_chart(fig_trend_tck, use_container_width=True, key="chart_trend_tackles")
                    
                with col_trend2:
                    st.markdown('<h4 style="color: #ffffff; font-size: 15px; font-weight: 700; margin-bottom: 10px;">📈 EVOLUCIÓN DE APOYOS EN RUCK Y QUIEBRES</h4>', unsafe_allow_html=True)
                    fig_trend_ruck = go.Figure()
                    fig_trend_ruck.add_trace(
                        go.Scatter(x=df_hist["Partido"], y=df_hist["Apoyos Ruck"], name="Apoyos Ruck", marker_color="#58a6ff", line=dict(width=3))
                    )
                    fig_trend_ruck.add_trace(
                        go.Scatter(x=df_hist["Partido"], y=df_hist["Quiebres"], name="Quiebres de Línea", marker_color="#3fb950", line=dict(width=3))
                    )
                    fig_trend_ruck.update_layout(
                        paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9",
                        height=300, margin=dict(l=40, r=40, t=10, b=10),
                        legend=dict(orientation="h", y=1.2, font=dict(color="#8b949e")),
                        yaxis=dict(gridcolor="#21262d", title="Cantidad")
                    )
                    fig_trend_ruck.update_xaxes(gridcolor="#21262d")
                    st.plotly_chart(fig_trend_ruck, use_container_width=True, key="chart_trend_rucks")
                    
                st.markdown('<h4 style="color: #ffffff; font-size: 15px; font-weight: 700; margin-top: 15px; margin-bottom: 10px;">📋 TABLA HISTÓRICA DEL TORNEO</h4>', unsafe_allow_html=True)
                st.dataframe(
                    df_hist[["Partido", "Puntos", "Tries", "Tackles", "% Tackles", "Quiebres", "Apoyos Ruck", "Penales Cometidos"]].style
                        .set_properties(**{"background-color": "#161b22", "color": "#ffffff", "border-bottom": "1px solid #30363d", "font-size": "14px", "padding": "8px"})
                        .set_table_styles([{"selector": "th", "props": [("background-color", "#161b22"),
                                            ("color", "#58a6ff"), ("font-weight", "700"),
                                            ("font-size", "13px"), ("text-transform", "uppercase"),
                                            ("border-bottom", "2px solid #30363d")]}]),
                    use_container_width=True, hide_index=True, key="df_indiv_hist"
                )


def _generar_pdf(**kw):
    """Genera un PDF completo del informe del partido con reportlab."""
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    # ── Paleta ──
    NEGRO    = colors.HexColor("#0d1117")
    AZUL     = colors.HexColor("#58a6ff")
    VERDE    = colors.HexColor("#3fb950")
    ROJO     = colors.HexColor("#f85149")
    GRIS_OSC = colors.HexColor("#161b22")
    GRIS_MED = colors.HexColor("#1c2030")
    GRIS_TXT = colors.HexColor("#c9d1d9")
    BLANCO   = colors.white
    AMARILLO = colors.HexColor("#e3b341")

    styles = getSampleStyleSheet()

    def st_title(text, color=BLANCO):
        return ParagraphStyle("t", fontSize=22, fontName="Helvetica-Bold",
                               textColor=color, alignment=TA_CENTER, spaceAfter=4)

    def st_h2(color=AZUL):
        return ParagraphStyle("h2", fontSize=13, fontName="Helvetica-Bold",
                               textColor=color, spaceBefore=14, spaceAfter=6)

    def st_normal():
        return ParagraphStyle("n", fontSize=9, fontName="Helvetica",
                               textColor=GRIS_TXT, spaceAfter=3)

    def st_small():
        return ParagraphStyle("s", fontSize=8, fontName="Helvetica",
                               textColor=colors.HexColor("#8b949e"), spaceAfter=2)

    def tabla_header_style():
        return TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), GRIS_OSC),
            ("TEXTCOLOR",   (0,0), (-1,0), AZUL),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,0), 8),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [GRIS_MED, NEGRO]),
            ("TEXTCOLOR",   (0,1), (-1,-1), GRIS_TXT),
            ("FONTSIZE",    (0,1), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#2d3748")),
            ("ROWHEIGHT",   (0,0), (-1,-1), 18),
            ("LEFTPADDING",  (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING",   (0,0), (-1,-1), 3),
            ("BOTTOMPADDING",(0,0), (-1,-1), 3),
        ])

    story = []
    W = A4[0] - 3.6*cm   # ancho util

    # ══ PORTADA ══
    story.append(Spacer(1, 0.5*cm))
    portada_data = [[Paragraph(
        f'<font color="#58a6ff"><b>CLUB UNIVERSITARIO DE LA PLATA</b></font><br/>'
        f'<font color="#c9d1d9" size="14">Informe de Partido</font><br/>'
        f'<font color="#8b949e" size="10">{kw["selected_match"]}</font>',
        ParagraphStyle("p", fontSize=20, fontName="Helvetica-Bold",
                        textColor=BLANCO, alignment=TA_CENTER)
    )]]
    t_portada = Table(portada_data, colWidths=[W])
    t_portada.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), NEGRO),
        ("ROUNDEDCORNERS", [12]),
        ("LEFTPADDING",  (0,0), (-1,-1), 20),
        ("RIGHTPADDING", (0,0), (-1,-1), 20),
        ("TOPPADDING",   (0,0), (-1,-1), 24),
        ("BOTTOMPADDING",(0,0), (-1,-1), 24),
        ("BOX",          (0,0), (-1,-1), 1.5, AZUL),
    ]))
    story.append(t_portada)
    story.append(Spacer(1, 0.6*cm))

    # ── Marcador ──
    story.append(Paragraph("RESULTADO", st_h2(AZUL)))
    story.append(HRFlowable(width=W, thickness=1, color=AZUL, spaceAfter=6))

    res_color = {"VICTORIA": VERDE, "DERROTA": ROJO, "EMPATE": AMARILLO}.get(kw["res_txt"], BLANCO)
    marc_data = [
        [Paragraph(f'<b>{kw["name_local"]}</b>', ParagraphStyle("ml", fontSize=14, fontName="Helvetica-Bold", textColor=AZUL, alignment=TA_CENTER)),
         Paragraph(f'<b>{kw["s_l"]}</b>', ParagraphStyle("sl", fontSize=28, fontName="Helvetica-Bold", textColor=BLANCO, alignment=TA_CENTER)),
         Paragraph(f'<b>vs</b>', ParagraphStyle("vs", fontSize=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#484f58"), alignment=TA_CENTER)),
         Paragraph(f'<b>{kw["s_r"]}</b>', ParagraphStyle("sr", fontSize=28, fontName="Helvetica-Bold", textColor=BLANCO, alignment=TA_CENTER)),
         Paragraph(f'<b>{kw["name_rival"]}</b>', ParagraphStyle("mr", fontSize=14, fontName="Helvetica-Bold", textColor=ROJO, alignment=TA_CENTER))],
        [Paragraph(f'{kw["t_l"]}T · {kw["g_l"]}G · {kw["p_l"]}P', ParagraphStyle("dl", fontSize=8, fontName="Helvetica", textColor=GRIS_TXT, alignment=TA_CENTER)),
         Paragraph(f'<font color="#{"3fb950" if kw["s_l"] > kw["s_r"] else "f85149" if kw["s_l"] < kw["s_r"] else "e3b341"}"><b>{kw["res_txt"]}</b></font>',
                   ParagraphStyle("res", fontSize=11, fontName="Helvetica-Bold", textColor=BLANCO, alignment=TA_CENTER)),
         "", "",
         Paragraph(f'{kw["t_r"]}T · {kw["g_r"]}G · {kw["p_r"]}P', ParagraphStyle("dr", fontSize=8, fontName="Helvetica", textColor=GRIS_TXT, alignment=TA_CENTER))],
    ]
    t_marc = Table(marc_data, colWidths=[W*0.25, W*0.15, W*0.2, W*0.15, W*0.25])
    t_marc.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), GRIS_OSC),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("SPAN",        (1,1), (3,1)),
        ("TOPPADDING",  (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("BOX",         (0,0), (-1,-1), 0.5, colors.HexColor("#30363d")),
    ]))
    story.append(t_marc)
    story.append(Spacer(1, 0.5*cm))

    # ── Tackles ──
    story.append(Paragraph("⚡ TACKLES", st_h2(AZUL)))
    story.append(HRFlowable(width=W, thickness=0.5, color=GRIS_OSC, spaceAfter=4))
    kpi_tck = [
        [Paragraph("Total", st_small()), Paragraph("Efectivos", st_small()),
         Paragraph("Fallados", st_small()), Paragraph("% Efectividad", st_small())],
        [Paragraph(f'<b>{kw["total_tackles"]}</b>', ParagraphStyle("v", fontSize=16, fontName="Helvetica-Bold", textColor=BLANCO, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#3fb950">{kw["total_buenos"]}</font></b>', ParagraphStyle("v2", fontSize=16, fontName="Helvetica-Bold", textColor=VERDE, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#f85149">{kw["total_tackles"]-kw["total_buenos"]}</font></b>', ParagraphStyle("v3", fontSize=16, fontName="Helvetica-Bold", textColor=ROJO, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#58a6ff">{kw["pct_efectividad"]}%</font></b>', ParagraphStyle("v4", fontSize=16, fontName="Helvetica-Bold", textColor=AZUL, alignment=TA_CENTER))],
    ]
    t_kpi_tck = Table(kpi_tck, colWidths=[W/4]*4)
    t_kpi_tck.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GRIS_MED),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#30363d")),
        ("LINEBELOW", (0,0), (-1,0), 1, AZUL),
    ]))
    story.append(t_kpi_tck)
    story.append(Spacer(1, 0.3*cm))

    if not kw["df_tck"].empty:
        df = kw["df_tck"].head(12)
        header = [["Jugador", "Total", "Efectivos", "Fallados", "Dobles", "% Efect."]]
        rows = [[r["Jugador"], r["Total"], r["Efectivos"], r["Fallados"], r["Dobles"], f'{r["% Efectividad"]}%']
                for _, r in df.iterrows()]
        t = Table(header + rows, colWidths=[W*0.4, W*0.12, W*0.12, W*0.12, W*0.12, W*0.12])
        t.setStyle(tabla_header_style())
        story.append(t)

    story.append(Spacer(1, 0.4*cm))

    # ── Quiebres + Scrums ──
    story.append(Paragraph("💥 QUIEBRES DE LÍNEA  |  🏟️ SCRUMS", st_h2(AZUL)))
    story.append(HRFlowable(width=W, thickness=0.5, color=GRIS_OSC, spaceAfter=4))

    col_izq, col_der = [], []
    if not kw["df_qbr"].empty:
        qhdr = [["Jugador", "Quiebres"]]
        qrows = [[r["Jugador"], r["Quiebres"]] for _, r in kw["df_qbr"].iterrows()]
        tq = Table(qhdr + qrows, colWidths=[W*0.22, W*0.1])
        tq.setStyle(tabla_header_style())
        story.append(tq)
    scrum_data = [
        [Paragraph("Scrums Nuestros", st_small()), Paragraph("Scrums Rival", st_small())],
        [Paragraph(f'<b><font color="#58a6ff">{kw["scrum_nuestros"]}</font></b>',
                   ParagraphStyle("sc", fontSize=18, fontName="Helvetica-Bold", textColor=AZUL, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#f85149">{kw["scrum_rival"]}</font></b>',
                   ParagraphStyle("sc2", fontSize=18, fontName="Helvetica-Bold", textColor=ROJO, alignment=TA_CENTER))],
    ]
    ts = Table(scrum_data, colWidths=[W/2, W/2])
    ts.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GRIS_MED),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#30363d")),
        ("LINEBELOW", (0,0), (-1,0), 1, AZUL),
    ]))
    story.append(Spacer(1, 0.2*cm))
    story.append(ts)
    story.append(Spacer(1, 0.4*cm))

    # ── Kicks ──
    story.append(Paragraph("🦵 KICKS POR JUGADOR", st_h2(AZUL)))
    story.append(HRFlowable(width=W, thickness=0.5, color=GRIS_OSC, spaceAfter=4))
    if not kw["df_kck"].empty:
        khdr = [["Jugador", "Total Kicks", "Gana Terreno", "Territorial", "% Efect."]]
        krows = [[r["Jugador"], r["Total Kicks"], r["Gana Terreno"], r["Territorial"], f'{r["% Efectividad"]}%']
                 for _, r in kw["df_kck"].iterrows()]
        tk = Table(khdr + krows, colWidths=[W*0.35, W*0.16, W*0.18, W*0.16, W*0.15])
        tk.setStyle(tabla_header_style())
        story.append(tk)
    story.append(Spacer(1, 0.4*cm))

    # ── Pesca ──
    story.append(Paragraph("🎣 PESCA (RESTART CONTEST)", st_h2(AZUL)))
    story.append(HRFlowable(width=W, thickness=0.5, color=GRIS_OSC, spaceAfter=4))
    pesca_kpi = [
        [Paragraph("Pesquemos", st_small()), Paragraph("Recuperadas", st_small()), Paragraph("Rival Pesca", st_small())],
        [Paragraph(f'<b>{kw["pesca_nosotros"]}</b>', ParagraphStyle("pk1", fontSize=16, fontName="Helvetica-Bold", textColor=BLANCO, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#3fb950">{kw["pesca_recupera"]}</font></b>', ParagraphStyle("pk2", fontSize=16, fontName="Helvetica-Bold", textColor=VERDE, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#f85149">{kw["pesca_rival"]}</font></b>', ParagraphStyle("pk3", fontSize=16, fontName="Helvetica-Bold", textColor=ROJO, alignment=TA_CENTER))],
    ]
    tp = Table(pesca_kpi, colWidths=[W/3]*3)
    tp.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GRIS_MED),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#30363d")),
        ("LINEBELOW", (0,0), (-1,0), 1, AZUL),
    ]))
    story.append(tp)
    story.append(Spacer(1, 0.4*cm))

    # ── Penales ──
    story.append(Paragraph("🟡 PENALES Y FREE KICKS", st_h2(AZUL)))
    story.append(HRFlowable(width=W, thickness=0.5, color=GRIS_OSC, spaceAfter=4))
    pen_kpi = [
        [Paragraph("Nuestros", st_small()), Paragraph("Rival", st_small())],
        [Paragraph(f'<b><font color="#f85149">{kw["pnl_u"]}</font></b>', ParagraphStyle("pp1", fontSize=18, fontName="Helvetica-Bold", textColor=ROJO, alignment=TA_CENTER)),
         Paragraph(f'<b>{kw["pnl_rival"]}</b>', ParagraphStyle("pp2", fontSize=18, fontName="Helvetica-Bold", textColor=BLANCO, alignment=TA_CENTER))],
    ]
    tpen = Table(pen_kpi, colWidths=[W/2, W/2])
    tpen.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GRIS_MED),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#30363d")),
        ("LINEBELOW", (0,0), (-1,0), 1, AZUL),
    ]))
    story.append(tpen)
    if not kw["df_causas"].empty:
        story.append(Spacer(1, 0.2*cm))
        chdr = [["Causa", "Total"]]
        crows = [[r["Causa"], r["Total"]] for _, r in kw["df_causas"].iterrows()]
        tc = Table(chdr + crows, colWidths=[W*0.75, W*0.25])
        tc.setStyle(tabla_header_style())
        story.append(tc)
    story.append(Spacer(1, 0.4*cm))

    # ── Line Out ──
    story.append(Paragraph("📏 LINE OUT", st_h2(AZUL)))
    story.append(HRFlowable(width=W, thickness=0.5, color=GRIS_OSC, spaceAfter=4))
    lin_kpi = [
        [Paragraph("Total Lines", st_small()), Paragraph("Propios", st_small()),
         Paragraph("Rivales", st_small()), Paragraph("P. Limpia", st_small()),
         Paragraph("Robadas", st_small()), Paragraph("Perdidas", st_small())],
        [Paragraph(f'<b>{kw["lin_total"]}</b>', ParagraphStyle("lk1", fontSize=14, fontName="Helvetica-Bold", textColor=AZUL, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#3fb950">{kw["lin_total_prop"]}</font></b>', ParagraphStyle("lk2", fontSize=14, fontName="Helvetica-Bold", textColor=VERDE, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#f85149">{kw["lin_total_riv"]}</font></b>', ParagraphStyle("lk3", fontSize=14, fontName="Helvetica-Bold", textColor=ROJO, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#3fb950">{kw["lin_limpia"]}</font></b>', ParagraphStyle("lk4", fontSize=14, fontName="Helvetica-Bold", textColor=VERDE, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#f85149">{kw["lin_robada"]}</font></b>', ParagraphStyle("lk5", fontSize=14, fontName="Helvetica-Bold", textColor=ROJO, alignment=TA_CENTER)),
         Paragraph(f'<b><font color="#e3b341">{kw["lin_perdida"]}</font></b>', ParagraphStyle("lk6", fontSize=14, fontName="Helvetica-Bold", textColor=AMARILLO, alignment=TA_CENTER))],
    ]
    tlin = Table(lin_kpi, colWidths=[W/6]*6)
    tlin.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GRIS_MED),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#30363d")),
        ("LINEBELOW", (0,0), (-1,0), 1, AZUL),
    ]))
    story.append(tlin)

    lin_det = [
        [Paragraph("Sucia", st_small()), Paragraph("Torcida", st_small()),
         Paragraph("Pasada", st_small()), Paragraph("Tiro Rápido", st_small())],
        [Paragraph(f'<b>{kw["lin_sucia"]}</b>', ParagraphStyle("ld1", fontSize=12, fontName="Helvetica-Bold", textColor=AMARILLO, alignment=TA_CENTER)),
         Paragraph(f'<b>{kw["lin_torcida"]}</b>', ParagraphStyle("ld2", fontSize=12, fontName="Helvetica-Bold", textColor=GRIS_TXT, alignment=TA_CENTER)),
         Paragraph(f'<b>{kw["lin_rapido"]}</b>', ParagraphStyle("ld3", fontSize=12, fontName="Helvetica-Bold", textColor=GRIS_TXT, alignment=TA_CENTER)),
         Paragraph(f'<b>{kw["lin_rapido"]}</b>', ParagraphStyle("ld4", fontSize=12, fontName="Helvetica-Bold", textColor=colors.HexColor("#a371f7"), alignment=TA_CENTER))],
    ]
    tlin2 = Table(lin_det, colWidths=[W/4]*4)
    tlin2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NEGRO),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#30363d")),
    ]))
    story.append(Spacer(1, 0.15*cm))
    story.append(tlin2)

    # ── Footer ──
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width=W, thickness=0.5, color=GRIS_OSC))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Club Universitario de La Plata · Sistema de Análisis de Rendimiento · 2026",
        ParagraphStyle("footer", fontSize=7, fontName="Helvetica",
                        textColor=colors.HexColor("#484f58"), alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


if __name__ == "__main__":
    rugby_analysis_module()
