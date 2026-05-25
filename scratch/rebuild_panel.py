import re

def main():
    with open('src/modules/panel_partido.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add _cargar_mapa_dni_nombres and _get_foto_b64
    if '_cargar_mapa_dni_nombres' not in content:
        dni_logic = """
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
    img_html = f'<img src="data:image/jpeg;base64,{foto_b64}" style="width:75px;height:75px;border-radius:50%;object-fit:cover;border:3px solid {color};margin-bottom:8px;"/>' if foto_b64 else f'<div style="width:75px;height:75px;border-radius:50%;background:#1c2030;border:3px solid {color};margin-bottom:8px;display:flex;align-items:center;justify-content:center;font-size:24px;color:#8b949e">👤</div>'
    
    return f'''
    <div style="background:#161b22; border:1px solid #30363d; border-radius:12px; padding:15px; text-align:center; display:flex; flex-direction:column; align-items:center; height:100%; border-top:4px solid {color}; box-shadow:0 4px 12px rgba(0,0,0,0.2)">
        {img_html}
        <div style="font-size:0.85rem;font-weight:700;color:#c9d1d9;max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{nombre}</div>
        <div style="font-size:2rem;font-weight:900;color:{color};line-height:1;margin:5px 0;">{stat_value}</div>
        <div style="font-size:0.75rem;color:#8b949e;text-transform:uppercase;font-weight:700;letter-spacing:1px;">{stat_label}</div>
    </div>
    '''

"""
        # Insert after _get_escudo_b64 definition
        content = re.sub(r'(def _get_escudo_b64.*?return base64.b64encode\(f.read\(\)\).decode\(\)\n)', r'\1\n' + dni_logic, content, flags=re.DOTALL)

    # 2. Líderes del Partido section
    lideres_code = """
    # ── LIDERES DEL PARTIDO ──
    mapa_dni = _cargar_mapa_dni_nombres()
    
    st.markdown('<div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #fff;"><h2 style="color: #fff; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;">🏆 LÍDERES DEL PARTIDO</h2></div>', unsafe_allow_html=True)
    
    lideres_cols = st.columns(4)
    
    with lideres_cols[0]:
        if not df_tck.empty:
            lider = df_tck.iloc[0]
            st.markdown(_player_card_html(lider["Jugador"], "Tackles", lider["Total"], "#e3b341", mapa_dni), unsafe_allow_html=True)
            
    with lideres_cols[1]:
        if not df_qbr.empty:
            lider = df_qbr.iloc[0]
            st.markdown(_player_card_html(lider["Jugador"], "Quiebres", lider["Quiebres"], "#3fb950", mapa_dni), unsafe_allow_html=True)
            
    with lideres_cols[2]:
        if not df_kck.empty:
            lider = df_kck.iloc[0]
            st.markdown(_player_card_html(lider["Jugador"], "Kicks", lider["Total Kicks"], "#a371f7", mapa_dni), unsafe_allow_html=True)
            
    with lideres_cols[3]:
        if not df_pnl_jug.empty:
            lider = df_pnl_jug.iloc[0]
            st.markdown(_player_card_html(lider["Jugador"], "Penales Cometidos", lider["Penales Cometidos"], "#f85149", mapa_dni), unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    """
    if "LÍDERES DEL PARTIDO" not in content:
        content = content.replace("    # ── TACKLES ──", lideres_code + "    # ── TACKLES ──")

    # 3. Tackles Section
    tackles_old = "    st.markdown('<div class=\"section-header\">⚡ Tackles por Jugador</div>', unsafe_allow_html=True)"
    tackles_new = "    st.markdown('<div style=\"background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #e3b341;\"><h2 style=\"color: #e3b341; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;\">⚡ TACKLES POR JUGADOR</h2></div>', unsafe_allow_html=True)"
    content = content.replace(tackles_old, tackles_new)
    
    # Tackles chart update
    content = content.replace('height=420', 'height=600')
    content = re.sub(
        r'(fig_tck.update_layout\(.*?)margin=dict\(l=0, r=20, t=10, b=10\)(.*?yaxis=dict\(autorange="reversed"\))',
        r'\1margin=dict(l=0, r=100, t=10, b=10)\2, font=dict(family="Arial Black", size=18)',
        content, flags=re.DOTALL
    )

    # Tackles donut update
    content = content.replace('textinfo="percent"', 'textinfo="label+percent"')
    content = content.replace('font=dict(size=32, color="#3fb950")', 'font=dict(size=38, color="#3fb950", weight=900)')
    content = content.replace('text=f"{pct_efectividad}%"', 'text=f"<span style=\'font-size:38px;font-weight:900;color:#3fb950\'>{pct_efectividad}%</span><br><span style=\'font-size:12px;color:#8b949e;font-weight:bold\'>EFECTIVIDAD</span>"')

    # Tackles dataframe
    content = content.replace('{"background-color": "#1c2030", "color": "#c9d1d9",\n                                   "border": "1px solid #2d3748", "font-size": "13px"}',
    '{"background-color": "#161b22", "color": "#ffffff", "border-bottom": "1px solid #30363d", "font-size": "18px", "padding": "12px"}')
    content = content.replace('"font-size", "11px"', '"font-size", "16px"')

    # 4. Quiebres
    quiebres_old = "    st.markdown('<div class=\"section-header\">💥 Quiebres de Línea</div>', unsafe_allow_html=True)"
    quiebres_new = "    st.markdown('<div style=\"background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #3fb950;\"><h2 style=\"color: #3fb950; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;\">💥 QUIEBRES DE LÍNEA</h2></div>', unsafe_allow_html=True)\\n        df_qbr = df_qbr[~df_qbr[\"Jugador\"].str.contains(\"Rival\", case=False, na=False)]"
    content = content.replace(quiebres_old, quiebres_new)
    
    content = re.sub(
        r'(fig_qbr = px.bar\(df_qbr.*?height=)280',
        r'\1 450',
        content, flags=re.DOTALL
    )
    content = re.sub(
        r'(fig_qbr.update_layout\(.*?yaxis=dict\(autorange="reversed"\))',
        r'\1, font=dict(family="Arial Black", size=16)',
        content, flags=re.DOTALL
    )

    # 5. Scrums
    scrums_old = "    st.markdown('<div class=\"section-header\">🏟️ Scrums</div>', unsafe_allow_html=True)"
    scrums_new = "    st.markdown('<div style=\"background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #58a6ff;\"><h2 style=\"color: #58a6ff; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;\">🏟️ SCRUMS</h2></div>', unsafe_allow_html=True)"
    content = content.replace(scrums_old, scrums_new)
    content = content.replace('textinfo="label+value+percent"', 'textinfo="label+percent"')
    content = content.replace('textfont=dict(size=13)', 'textfont=dict(family="Arial Black", size=14, color="white")')
    content = content.replace('text=f"{total_scrums}<br><span style=\'font-size:11px\'>total</span>"', 'text=f"<span style=\'font-size:38px;font-weight:900;color:#58a6ff\'>{total_scrums}</span><br><span style=\'font-size:12px;color:#8b949e;font-weight:bold\'>TOTAL SCRUMS</span>"')
    content = re.sub(r'(fig_scr.update_layout\(.*?height=)280', r'\1 450', content, flags=re.DOTALL)
    content = content.replace('showlegend=True', 'showlegend=False')

    # 6. Kicks
    kicks_old = "    st.markdown('<div class=\"section-header\">🦵 Kicks por Jugador</div>', unsafe_allow_html=True)"
    kicks_new = "    st.markdown('<div style=\"background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #a371f7;\"><h2 style=\"color: #a371f7; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;\">🦵 KICKS POR JUGADOR</h2></div>', unsafe_allow_html=True)"
    content = content.replace(kicks_old, kicks_new)
    content = re.sub(r'(fig_kck.update_layout\(.*?height=)320', r'\1 450', content, flags=re.DOTALL)
    content = re.sub(
        r'(fig_kck.update_layout\(.*?legend=dict\(orientation="h", y=1.1\))',
        r'\1, font=dict(family="Arial Black", size=14)',
        content, flags=re.DOTALL
    )

    # 7. Pesca
    pesca_old = "    st.markdown('<div class=\"section-header\">🎣 Pesca (Restart Contest)</div>', unsafe_allow_html=True)"
    pesca_new = "    st.markdown('<div style=\"background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #1f6feb;\"><h2 style=\"color: #1f6feb; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;\">🎣 PESCA (RESTART CONTEST)</h2></div>', unsafe_allow_html=True)"
    content = content.replace(pesca_old, pesca_new)
    content = content.replace('col7, col8, col9 = st.columns(3)', 'col7, col8, col9 = st.columns([1, 2, 2])')
    content = re.sub(r'(fig_psc.update_layout\(.*?height=)240', r'\1 350', content, flags=re.DOTALL)
    content = re.sub(
        r'(fig_psc.update_layout\(.*?yaxis=dict\(autorange="reversed"\))',
        r'\1, font=dict(family="Arial Black", size=14)',
        content, flags=re.DOTALL
    )

    # 8. Penales
    penales_old = "    st.markdown('<div class=\"section-header\">🟡 Penales y Free Kicks</div>', unsafe_allow_html=True)"
    penales_new = "    st.markdown('<div style=\"background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #e3b341;\"><h2 style=\"color: #e3b341; font-size: 28px; margin: 0; font-weight: 900; letter-spacing: 1px;\">🟡 PENALES Y FREE KICKS</h2></div>', unsafe_allow_html=True)"
    content = content.replace(penales_old, penales_new)
    
    # Delete fig_causas code and update columns
    content = re.sub(r'c10, c11, c12 = st.columns\(\[1, 2, 2\]\)(.*?)with c12:', r'c10, c11 = st.columns([2, 3])\1with c11:', content, flags=re.DOTALL)
    content = re.sub(r'with c11:\s*if not df_causas\.empty:.*?st\.plotly_chart\(fig_causas, use_container_width=True, key="chart_causas"\)\s*', '', content, flags=re.DOTALL)

    content = content.replace('textinfo="value"', 'textinfo="label+value"')
    content = re.sub(
        r'(fig_pnl_donut.update_layout\(.*?height=)240',
        r'\1 350, font=dict(family="Arial Black", size=14)',
        content, flags=re.DOTALL
    )
    content = re.sub(
        r'(fig_pnl_jug.update_layout\(.*?height=)280',
        r'\1 350, font=dict(family="Arial Black", size=14)',
        content, flags=re.DOTALL
    )
    
    # Add central text to fig_pnl_donut
    content = re.sub(r'(fig_pnl_donut.update_layout\()', r'fig_pnl_donut.add_annotation(text=f"<span style=\'font-size:38px;font-weight:900;color:#e3b341\'>{pnl_total}</span><br><span style=\'font-size:12px;color:#8b949e;font-weight:bold\'>TOTAL</span>", showarrow=False)\n        \1', content)


    with open('src/modules/panel_partido.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
