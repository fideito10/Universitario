import os
import re
from collections import defaultdict
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from src.utils.credentials import get_service_account_credentials

def rugby_analysis_module():
    # ─────────────────────────────────────────────
    # LÓGICA DE PROCESAMIENTO
    # ─────────────────────────────────────────────
    
    def get_int(val):
        if val is None or val == "": return 0
        try:
            if isinstance(val, str): val = val.replace(',', '.')
            return int(float(val))
        except: return 0

    def clean_player(name):
        if not name: return None
        name = str(name).strip()
        name = re.sub(r"^\d+[-.\s]+", "", name).strip()
        if not name or name.lower() in ["player", "nan", "jugador", "null"]: return None
        return name.title()

    def parse_sheet_data(rows_list):
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

    # Configuración de Hoja
    SHEET_ID = "1JXKJkDYcrOHRQ4fmC1uPkEW4crLNdJhzJLcwbMdOICU"

    def get_all_matches():
        try:
            creds = get_service_account_credentials()
            if not creds: return []
            client = gspread.authorize(creds)
            sh = client.open_by_key(SHEET_ID)
            return [ws.title for ws in sh.worksheets()]
        except: return []

    @st.cache_data(ttl=300)
    def load_match_data(match_name):
        try:
            creds = get_service_account_credentials()
            if not creds: return None
            client = gspread.authorize(creds)
            sh = client.open_by_key(SHEET_ID)
            rows = sh.worksheet(match_name).get_all_values()
            return parse_sheet_data(rows)
        except Exception as e:
            st.error(f"Error cargando {match_name}: {e}")
            return None

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
        data = load_match_data(selected_match)
    
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
    NAME_RIVAL = TEAM_RIVAL.split("(")[0].replace("006","").strip() if "006" in TEAM_RIVAL else TEAM_RIVAL
    if not NAME_RIVAL or NAME_RIVAL.upper() == "RIVAL": NAME_RIVAL = "Rival"
    
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
    tck_rows = find_rows("TACKLE")
    tck_map = defaultdict(lambda: {"ok": 0, "fail": 0})
    for r in tck_rows:
        p = clean_player(r.get("player") or r.get("name") or r.get("jugador"))
        if p and (not r.get("team") or r.get("team") == TEAM_LOCAL):
            tck_map[p]["ok"] += get_int(r.get("bueno") or r.get("bien (detiene)") or r.get("ok", 0))
            tck_map[p]["fail"] += get_int(r.get("malo") or r.get("mal (falla)") or r.get("fail", 0))
    df_tck = pd.DataFrame([{"Jugador": k, "Total": v["ok"]+v["fail"], "Efectivos": v["ok"], "Fallados": v["fail"]} for k,v in tck_map.items()])
    total_tackles, total_buenos, pct_efectividad = 0, 0, 0
    if not df_tck.empty:
        df_tck["% Efectividad"] = (df_tck["Efectivos"] / df_tck["Total"].replace(0, 1) * 100).round(1)
        df_tck = df_tck.sort_values("Total", ascending=False)
        total_tackles, total_buenos = df_tck["Total"].sum(), df_tck["Efectivos"].sum()
        pct_efectividad = pct_l(total_buenos, total_tackles)

    # 2) QUIEBRES
    qbr_rows = find_rows("QUIEBRE")
    qbr_map = defaultdict(int)
    for r in qbr_rows:
        p = clean_player(r.get("player") or r.get("jugador") or r.get("name"))
        if p and (not r.get("team") or r.get("team") == TEAM_LOCAL): qbr_map[p] += 1
    df_qbr = pd.DataFrame([{"Jugador": k, "Quiebres": v} for k,v in qbr_map.items()]).sort_values("Quiebres", ascending=False)

    # 3) KICKS
    kck_rows = find_rows("KICK")
    kck_map = defaultdict(lambda: {"gana": 0, "terr": 0})
    for r in kck_rows:
        p = clean_player(r.get("player") or r.get("jugador") or r.get("name"))
        if p and (not r.get("team") or r.get("team") == TEAM_LOCAL):
            kck_map[p]["gana"] += get_int(r.get("gana terreno") or r.get("ok", 0))
            kck_map[p]["terr"] += get_int(r.get("territorial", 0))
    kck_list = []
    for k, v in kck_map.items():
        tot = v["gana"] + v["terr"]
        kck_list.append({"Jugador": k, "Total Kicks": tot, "Gana Terreno": v["gana"], "Territorial": v["terr"], "% Efectividad": pct_l(v["gana"], tot)})
    df_kck = pd.DataFrame(kck_list).sort_values("Total Kicks", ascending=False)

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
    df_psc = pd.DataFrame([{"Jugador": k, "Total": v["total"], "Recupera": v["rec"]} for k,v in psc_jug.items()]).sort_values("Total", ascending=False)

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
    df_causas = pd.DataFrame([{"Causa": k, "Total": v} for k,v in causas.items()]).sort_values("Total", ascending=False)
    df_pnl_jug = pd.DataFrame([{"Jugador": k, "Penales Cometidos": v} for k,v in jug_pnl.items()]).sort_values("Penales Cometidos", ascending=False)
    total_penales, total_pescas = pnl_u, pesca_recupera
    total_enf = sum(1 for r in find_rows("FORZADO") if not r.get("team") or r.get("team") == TEAM_LOCAL)

    # 6) LINE OUT
    lin_rows = find_rows("LINE")
    lin_prop = [r for r in lin_rows if "PROPIO" in str(r.get("quien","")).upper() or r.get("team") == TEAM_LOCAL]
    lin_total_prop = len(lin_prop)
    lin_limpia_prop = sum(1 for r in lin_prop if "LIMPIA" in str(r.get("resultado","")).upper() or get_int(r.get("limpia",0)))
    lin_perdida_prop = sum(1 for r in lin_prop if "PERDIDA" in str(r.get("resultado","")).upper() or get_int(r.get("perdida",0)))
    lin_robada_prop = sum(1 for r in lin_prop if "ROBADA" in str(r.get("resultado","")).upper() or get_int(r.get("robada",0)))
    lin_riv = [r for r in lin_rows if "RIVAL" in str(r.get("quien","")).upper() or r.get("team") == TEAM_RIVAL]
    lin_total_riv = len(lin_riv)
    lin_limpia_riv = sum(1 for r in lin_riv if "LIMPIA" in str(r.get("resultado","")).upper())
    lin_robada_riv = sum(1 for r in lin_riv if "ROBADA" in str(r.get("resultado","")).upper())
    lin_perdida_riv = lin_total_riv - lin_limpia_riv - lin_robada_riv

    # Renderizado UI
    with st.container():
        st.markdown(f"""
        <div class="rugby-panel">
            <div class="hero">
                <div style="font-size:3rem">🏆</div>
                <div><div class="hero-title">Resumen de Partido</div><div class="hero-sub">{NAME_LOCAL} vs {NAME_RIVAL}</div></div>
            </div>
            <div class="scoreboard">
                <div class="score-teams">
                    <div class="team-block"><div class="team-name">{NAME_LOCAL}</div><div class="team-score">{s_l}</div><div class="score-detail">{t_l}T · {g_l}G · {p_l}P</div></div>
                    <div class="score-dash">vs</div>
                    <div class="team-block"><div class="team-name">{NAME_RIVAL}</div><div class="team-score">{s_r}</div><div class="score-detail">{t_r}T · {g_r}G · {p_r}P</div></div>
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

    # ── TACKLES ──
    st.markdown('<div class="section-header">⚡ Tackles por Jugador</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 2])
    with col1:
        fig_tck = px.bar(df_tck.head(12), x="Total", y="Jugador", orientation="h", color="% Efectividad",
                         color_continuous_scale=["#f85149", "#e3b341", "#3fb950"], range_color=[40, 100],
                         labels={"Total": "N° Tackles", "Jugador": ""}, text="Total")
        fig_tck.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=420,
                              margin=dict(l=0, r=20, t=10, b=10), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_tck, use_container_width=True)
    with col2:
        fig_donut = go.Figure(go.Pie(labels=["Efectivos", "Fallados"], values=[total_buenos, total_tackles-total_buenos],
                                     hole=0.65, marker_colors=["#3fb950", "#f85149"], textinfo="percent"))
        fig_donut.add_annotation(text=f"{pct_efectividad}%", font=dict(size=32, color="#3fb950"), showarrow=False)
        fig_donut.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=280,
                                margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig_donut, use_container_width=True)
        st.dataframe(df_tck[["Jugador","Total","Efectivos","Fallados","% Efectividad"]].head(8), use_container_width=True, hide_index=True)

    # ── QUIEBRES ──
    st.markdown('<div class="section-header">💥 Quiebres de Línea</div>', unsafe_allow_html=True)
    col3, col4 = st.columns([2, 3])
    with col3:
        if not df_qbr.empty:
            fig_qbr = px.bar(df_qbr, x="Quiebres", y="Jugador", orientation="h", color="Quiebres",
                             color_continuous_scale=["#1f6feb", "#58a6ff"], text="Quiebres")
            fig_qbr.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=280,
                                  margin=dict(l=0, r=0, t=10, b=10), showlegend=False, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_qbr, use_container_width=True)
        else: st.info("Sin datos de quiebres")
    with col4:
        if qbr_rows:
            detalle = []
            for r in qbr_rows:
                pn = clean_player(r.get("Player") or r.get("jugador") or r.get("name")) or "Sin ID"
                tipo = "Fija" if get_int(r.get("Fija",0)) else ("Móvil" if get_int(r.get("Movil",0)) else "Libre")
                res_q = "Marca Puntos 🏆" if get_int(r.get("Marca puntos",0)) else ("Conecta 🔗" if get_int(r.get("Conecta compañero",0)) else ("Mantiene 🔒" if get_int(r.get("Mantiene posesión",0)) else "Pierde ❌"))
                detalle.append({"Jugador": pn, "Tipo": tipo, "Resultado": res_q})
            st.dataframe(pd.DataFrame(detalle), use_container_width=True, hide_index=True, height=250)

    # ── KICKS ──
    st.markdown('<div class="section-header">🦵 Kicks por Jugador</div>', unsafe_allow_html=True)
    col5, col6 = st.columns([3, 2])
    with col5:
        fig_kck = px.bar(df_kck, x="Jugador", y=["Gana Terreno", "Territorial"], barmode="group",
                         color_discrete_map={"Gana Terreno": "#3fb950", "Territorial": "#58a6ff"}, text_auto=True)
        fig_kck.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=320,
                              margin=dict(l=0, r=0, t=10, b=10), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_kck, use_container_width=True)
    with col6: st.dataframe(df_kck[["Jugador","Total Kicks","Gana Terreno","Territorial","% Efectividad"]], use_container_width=True, hide_index=True)

    # ── PESCA ──
    st.markdown('<div class="section-header">🎣 Pesca (Restart Contest)</div>', unsafe_allow_html=True)
    col7, col8, col9 = st.columns(3)
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
            fig_psc.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=240,
                                  margin=dict(l=0, r=0, t=10, b=10), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_psc, use_container_width=True)
    with col9: st.dataframe(df_psc, use_container_width=True, hide_index=True)

    # ── PENALES ──
    st.markdown('<div class="section-header">🟡 Penales y Free Kicks</div>', unsafe_allow_html=True)
    c10, c11, c12 = st.columns([1, 2, 2])
    with c10:
        fig_pnl_donut = go.Figure(go.Pie(labels=["A favor", "En contra"], values=[pnl_u, pnl_rival], hole=0.6,
                                         marker_colors=["#3fb950", "#f85149"], textinfo="value"))
        fig_pnl_donut.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=240, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig_pnl_donut, use_container_width=True)
    with c11:
        if not df_causas.empty:
            fig_causas = px.bar(df_causas, x="Total", y="Causa", orientation="h", text="Total", color_discrete_sequence=["#f85149"])
            fig_causas.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=280, margin=dict(l=0, r=0, t=10, b=10), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_causas, use_container_width=True)
    with c12:
        if not df_pnl_jug.empty:
            fig_pnl_jug = px.bar(df_pnl_jug, x="Penales Cometidos", y="Jugador", orientation="h", text="Penales Cometidos", color_discrete_sequence=["#e3b341"])
            fig_pnl_jug.update_layout(paper_bgcolor="#161b22", plot_bgcolor="#161b22", font_color="#c9d1d9", height=280, margin=dict(l=0, r=0, t=10, b=10), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_pnl_jug, use_container_width=True)

    # ── LINE ──
    st.markdown('<div class="section-header">📏 Line Out</div>', unsafe_allow_html=True)
    c13, c14 = st.columns(2)
    with c13:
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin-bottom:12px">
            <div style="font-size:0.85rem;color:#58a6ff;font-weight:700;margin-bottom:12px">🔵 Lines Propias ({lin_total_prop})</div>
            <div style="color:#c9d1d9;font-size:0.9rem">✅ Limpia: {lin_limpia_prop} | ❌ Perdida: {lin_perdida_prop} | 🔄 Robada: {lin_robada_prop}</div>
        </div>
        """, unsafe_allow_html=True)
    with c14:
        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin-bottom:12px">
            <div style="font-size:0.85rem;color:#f85149;font-weight:700;margin-bottom:12px">🔴 Lines Rivales ({lin_total_riv})</div>
            <div style="color:#c9d1d9;font-size:0.9rem">✅ Limpia: {lin_limpia_riv} | 🔄 Robada: {lin_robada_riv}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""<div style="text-align:center; color:#484f58; font-size:0.8rem; margin-top:50px; padding:20px; border-top:1px solid #21262d">Club Universitario de La Plata · Sistema de Rendimiento</div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    rugby_analysis_module()
