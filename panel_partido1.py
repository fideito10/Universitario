"""
panel_partido.py
----------------
Panel deportivo del análisis de partido — Club Universitario de La Plata
Ejecutar con:  streamlit run panel_partido.py
"""

import os
import re
from collections import defaultdict
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# CSS PREMIUM
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Análisis de Partido — CULP",
    page_icon="🏉",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Fondo oscuro */
.stApp { background: #0d1117; color: #e6edf3; }

/* Ocultar elementos Streamlit */
#MainMenu, footer, header { visibility: hidden; }

/* Hero banner */
.hero {
    background: linear-gradient(135deg, #1a2744 0%, #0d1117 60%, #1a0a2e 100%);
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 24px;
}
.hero-title { font-size: 2.2rem; font-weight: 900; color: #f0f6fc; margin: 0; }
.hero-sub   { font-size: 1rem; color: #8b949e; margin: 4px 0 0 0; }

/* Scoreboard */
.scoreboard {
    background: linear-gradient(135deg, #161b22, #1c2030);
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 28px;
    text-align: center;
    margin-bottom: 24px;
}
.score-teams { display: flex; justify-content: space-around; align-items: center; gap: 16px; }
.team-block  { flex: 1; }
.team-name   { font-size: 1rem; font-weight: 600; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
.team-score  { font-size: 4rem; font-weight: 900; line-height: 1; margin: 8px 0; }
.score-local  { color: #58a6ff; }
.score-rival  { color: #f85149; }
.score-dash   { font-size: 2.5rem; font-weight: 300; color: #484f58; }
.score-detail { font-size: 0.8rem; color: #6e7681; margin-top: 8px; }

/* KPI Cards */
.kpi-grid { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.kpi-card {
    flex: 1; min-width: 140px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 16px;
    text-align: center;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: #58a6ff; }
.kpi-value { font-size: 2.4rem; font-weight: 900; color: #58a6ff; line-height: 1; }
.kpi-label { font-size: 0.78rem; color: #8b949e; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-sub   { font-size: 0.85rem; color: #3fb950; margin-top: 4px; font-weight: 600; }

/* Section header */
.section-header {
    font-size: 1.1rem; font-weight: 700; color: #f0f6fc;
    border-left: 4px solid #58a6ff;
    padding-left: 12px;
    margin: 28px 0 16px 0;
    text-transform: uppercase; letter-spacing: 0.5px;
}

/* Table override */
.stDataFrame { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PARSER (mismo que parse_partido.py)
# ─────────────────────────────────────────────
@st.cache_data
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

def get_int(val):
    try: return int(val)
    except: return 0

def clean_player(name: str) -> str:
    name = name.strip()
    # "9-D'ONOFRIO LORENZO" → "D'ONOFRIO LORENZO"
    name = re.sub(r"^\d+-", "", name).strip()
    if not name or name.lower().startswith("player"):
        return None
    return name.title()

# ─────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────
CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "006 ADF - 006 CULP (ADF) (0-0) PRIMERA A 2026 (1).csv"
)

if not os.path.exists(CSV):
    st.error(f"❌ No se encontró el archivo CSV en: {CSV}")
    st.stop()

data = parse_csv(CSV)

TEAM_LOCAL = "006 CULP (ADF)"
TEAM_RIVAL = "006 ADF"
NAME_LOCAL  = "Universitario"
NAME_RIVAL  = "ADF"

# ─────────────────────────────────────────────
# CALCULOS
# ─────────────────────────────────────────────

# 1) PUNTOS
pts_rows = data.get("12 PUNTOS (-)", {}).get("rows", [])
tries_l  = sum(get_int(r.get("try",  0)) for r in pts_rows if r.get("Team","") == TEAM_LOCAL)
goals_l  = sum(get_int(r.get("goal", 0)) for r in pts_rows if r.get("Team","") == TEAM_LOCAL)
penal_l  = sum(get_int(r.get("penal",0)) for r in pts_rows if r.get("Team","") == TEAM_LOCAL)
tries_r  = sum(get_int(r.get("try",  0)) for r in pts_rows if r.get("Team","") == TEAM_RIVAL)
goals_r  = sum(get_int(r.get("goal", 0)) for r in pts_rows if r.get("Team","") == TEAM_RIVAL)
penal_r  = sum(get_int(r.get("penal",0)) for r in pts_rows if r.get("Team","") == TEAM_RIVAL)
score_l  = tries_l*5 + goals_l*2 + penal_l*3
score_r  = tries_r*5 + goals_r*2 + penal_r*3

# 2) TACKLES por jugador
tck_rows = data.get("1 TACKLE", {}).get("rows", [])
tackles_por_jugador = defaultdict(lambda: {"total": 0, "buenos": 0, "malos": 0, "doble": 0})
for r in tck_rows:
    jugadores = [j.strip() for j in r.get("Player", "").split("|") if j.strip()]
    for p in jugadores:
        pn = clean_player(p)
        if pn:
            tackles_por_jugador[pn]["total"]  += 1
            tackles_por_jugador[pn]["buenos"] += get_int(r.get("Bien (detiene)", 0))
            tackles_por_jugador[pn]["malos"]  += get_int(r.get("Mal (Falla)", 0))
            tackles_por_jugador[pn]["doble"]  += get_int(r.get("Doble Tackle", 0))

total_tackles = sum(d["total"] for d in tackles_por_jugador.values())
total_buenos  = sum(d["buenos"] for d in tackles_por_jugador.values())

df_tck = pd.DataFrame([
    {"Jugador": p,
     "Total": d["total"],
     "Efectivos": d["buenos"],
     "Fallados": d["malos"],
     "Dobles": d["doble"],
     "% Efectividad": round(d["buenos"]/d["total"]*100) if d["total"] else 0}
    for p, d in tackles_por_jugador.items()
]).sort_values("Total", ascending=False).reset_index(drop=True)

# 3) QUIEBRES
qbr_rows = data.get("4 QUIEBRES", {}).get("rows", [])
quiebres_por_jugador = defaultdict(int)
for r in qbr_rows:
    pn = clean_player(r.get("Player", ""))
    if pn:
        quiebres_por_jugador[pn] += 1

total_quiebres = len(qbr_rows)
df_qbr = pd.DataFrame([
    {"Jugador": p, "Quiebres": n}
    for p, n in sorted(quiebres_por_jugador.items(), key=lambda x: -x[1])
])

# 4) KICKS
kck_rows = data.get("10 KICKS (.)", {}).get("rows", [])
kicks_por_jugador = defaultdict(lambda: {"total": 0, "gana": 0, "territorial": 0})
for r in kck_rows:
    pn = clean_player(r.get("Player", ""))
    if pn:
        kicks_por_jugador[pn]["total"]      += 1
        kicks_por_jugador[pn]["gana"]       += get_int(r.get("gana terreno", 0))
        kicks_por_jugador[pn]["territorial"]+= get_int(r.get("territorial", 0))

total_kicks   = len(kck_rows)
total_gana    = sum(get_int(r.get("gana terreno", 0)) for r in kck_rows)
total_territ  = sum(get_int(r.get("territorial", 0)) for r in kck_rows)

df_kck = pd.DataFrame([
    {"Jugador": p,
     "Total Kicks": d["total"],
     "Gana Terreno": d["gana"],
     "Territorial": d["territorial"],
     "% Efectividad": round(d["gana"]/d["total"]*100) if d["total"] else 0}
    for p, d in kicks_por_jugador.items()
]).sort_values("Total Kicks", ascending=False).reset_index(drop=True)

# 5) PESCA (11 PESCA)
psc_rows = data.get("11 PESCA (0)", {}).get("rows", [])
pesca_total     = len(psc_rows)
pesca_nosotros  = sum(get_int(r.get("Nosotros", 0)) for r in psc_rows)
pesca_rival     = sum(get_int(r.get("Rival", 0))    for r in psc_rows)
pesca_recupera  = sum(get_int(r.get("Recuperamos", 0)) for r in psc_rows)
pesca_penal_u   = sum(get_int(r.get("Penal para U", 0)) for r in psc_rows)

pesca_por_jugador = defaultdict(lambda: {"total": 0, "recupera": 0})
for r in psc_rows:
    pn = clean_player(r.get("Player", ""))
    if pn:
        pesca_por_jugador[pn]["total"]   += 1
        pesca_por_jugador[pn]["recupera"] += get_int(r.get("Recuperamos", 0))

df_psc = pd.DataFrame([
    {"Jugador": p, "Total": d["total"], "Recupera": d["recupera"]}
    for p, d in pesca_por_jugador.items()
]).sort_values("Total", ascending=False).reset_index(drop=True)

# 6) PENALES (7 PENALES Y FK)
pnl_rows = data.get("7 PENALES Y FK", {}).get("rows", [])
pnl_u     = sum(get_int(r.get("para U",     0)) for r in pnl_rows)
pnl_rival = sum(get_int(r.get("para Rival", 0)) for r in pnl_rows)
pnl_total = pnl_u + pnl_rival

# Causas
causas_keys = [
    ("Off side",                  "Off Side"),
    ("Tackle peligroso",          "Tackle Peligroso"),
    ("Retiene pelota en tackle",  "Retiene en Tackle"),
    ("Infraccion en ruck",        "Infracción en Ruck"),
    ("Juega desde el piso",       "Juega desde el Piso"),
    ("Infraccion en scrum",       "Infracción en Scrum"),
    ("Infraccion en line",        "Infracción en Line"),
    ("Obstruccion/pantalla",      "Obstrucción"),
]
df_causas = pd.DataFrame([
    {"Causa": label, "Total": sum(get_int(r.get(k, 0)) for r in pnl_rows)}
    for k, label in causas_keys
    if sum(get_int(r.get(k, 0)) for r in pnl_rows) > 0
]).sort_values("Total", ascending=False)

# Penales por jugador (causante)
pnl_por_jugador = defaultdict(int)
for r in pnl_rows:
    if get_int(r.get("para Rival", 0)):   # penal NUESTRO = infracción nuestra
        pn = clean_player(r.get("Player", ""))
        if pn:
            pnl_por_jugador[pn] += 1

df_pnl_jug = pd.DataFrame([
    {"Jugador": p, "Penales Cometidos": n}
    for p, n in sorted(pnl_por_jugador.items(), key=lambda x: -x[1])
]) if pnl_por_jugador else pd.DataFrame()

# 7) LINE (5 LINE)
lin_rows  = data.get("5 LINE", {}).get("rows", [])
lin_prop  = [r for r in lin_rows if get_int(r.get("Propio", 0))]
lin_rival = [r for r in lin_rows if get_int(r.get("Rival",  0))]

lin_total_prop  = len(lin_prop)
lin_limpia_prop = sum(get_int(r.get("Pelota Limpia", 0)) for r in lin_prop)
lin_perdida_prop= sum(get_int(r.get("Perdida",       0)) for r in lin_prop)
lin_robada_prop = sum(get_int(r.get("Robada",        0)) for r in lin_prop)

lin_total_riv   = len(lin_rival)
lin_limpia_riv  = sum(get_int(r.get("Pelota Limpia", 0)) for r in lin_rival)
lin_perdida_riv = sum(get_int(r.get("Perdida",       0)) for r in lin_rival)
lin_robada_riv  = sum(get_int(r.get("Robada",        0)) for r in lin_rival)

pct_l = lambda n, d: round(n/d*100) if d else 0

# ─────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────

# Hero
st.markdown(f"""
<div class="hero">
    <div style="font-size:3rem">🏉</div>
    <div>
        <div class="hero-title">Análisis de Partido</div>
        <div class="hero-sub">Club Universitario de La Plata · Primera A 2026</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── SCOREBOARD ──
result_text = "Victoria 🟢" if score_l > score_r else ("Derrota 🔴" if score_l < score_r else "Empate 🟡")
st.markdown(f"""
<div class="scoreboard">
    <div class="score-teams">
        <div class="team-block">
            <div class="team-name">{NAME_LOCAL}</div>
            <div class="team-score score-local">{score_l}</div>
            <div class="score-detail">{tries_l}T  {goals_l}G  {penal_l}P</div>
        </div>
        <div style="text-align:center">
            <div class="score-dash">–</div>
            <div style="font-size:0.85rem; color:#58a6ff; margin-top:6px; font-weight:700">{result_text}</div>
        </div>
        <div class="team-block">
            <div class="team-name">{NAME_RIVAL}</div>
            <div class="team-score score-rival">{score_r}</div>
            <div class="score-detail">{tries_r}T  {goals_r}G  {penal_r}P</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI ROW ──
pct_efectividad = round(total_buenos / total_tackles * 100) if total_tackles else 0
pct_kicks_ok    = round(total_gana   / total_kicks   * 100) if total_kicks   else 0

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-value">{total_tackles}</div>
        <div class="kpi-label">Total Tackles</div>
        <div class="kpi-sub">{pct_efectividad}% efectivos</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-value">{total_buenos}</div>
        <div class="kpi-label">Tackles Efectivos</div>
        <div class="kpi-sub">{total_tackles - total_buenos} fallados</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-value">{total_quiebres}</div>
        <div class="kpi-label">Quiebres de Línea</div>
        <div class="kpi-sub">{tries_l} tries anotados</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-value">{total_kicks}</div>
        <div class="kpi-label">Total Kicks</div>
        <div class="kpi-sub">{pct_kicks_ok}% gana terreno</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-value">{total_territ}</div>
        <div class="kpi-label">Kicks Territoriales</div>
        <div class="kpi-sub">de {total_kicks} totales</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── TACKLES ──
st.markdown('<div class="section-header">⚡ Tackles por Jugador</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 2])
with col1:
    fig_tck = px.bar(
        df_tck.head(12),
        x="Total", y="Jugador",
        orientation="h",
        color="% Efectividad",
        color_continuous_scale=["#f85149", "#e3b341", "#3fb950"],
        range_color=[40, 100],
        labels={"Total": "N° Tackles", "Jugador": ""},
        text="Total",
    )
    fig_tck.update_layout(
        paper_bgcolor="#161b22", plot_bgcolor="#161b22",
        font_color="#c9d1d9",
        height=420,
        margin=dict(l=0, r=20, t=10, b=10),
        coloraxis_colorbar=dict(title="% Efect.", tickfont=dict(color="#8b949e")),
        xaxis=dict(gridcolor="#21262d"),
        yaxis=dict(autorange="reversed"),
    )
    fig_tck.update_traces(textfont_color="#fff", textposition="outside")
    st.plotly_chart(fig_tck, use_container_width=True)

with col2:
    # Donut efectividad
    fig_donut = go.Figure(go.Pie(
        labels=["Efectivos", "Fallados"],
        values=[total_buenos, total_tackles - total_buenos],
        hole=0.65,
        marker_colors=["#3fb950", "#f85149"],
        textinfo="percent",
        textfont_size=14,
    ))
    fig_donut.add_annotation(
        text=f"{pct_efectividad}%",
        font=dict(size=32, color="#3fb950", family="Inter"),
        showarrow=False
    )
    fig_donut.update_layout(
        paper_bgcolor="#161b22", plot_bgcolor="#161b22",
        font_color="#c9d1d9",
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(font=dict(color="#8b949e")),
        title=dict(text="Efectividad en Tackle", font=dict(color="#8b949e", size=13), x=0.5),
    )
    st.plotly_chart(fig_donut, use_container_width=True)

    st.dataframe(
        df_tck[["Jugador","Total","Efectivos","Fallados","% Efectividad"]].head(8),
        use_container_width=True,
        hide_index=True,
    )

# ── QUIEBRES ──
st.markdown('<div class="section-header">💥 Quiebres de Línea</div>', unsafe_allow_html=True)

col3, col4 = st.columns([2, 3])
with col3:
    if not df_qbr.empty:
        fig_qbr = px.bar(
            df_qbr,
            x="Quiebres", y="Jugador",
            orientation="h",
            color="Quiebres",
            color_continuous_scale=["#1f6feb", "#58a6ff"],
            text="Quiebres",
        )
        fig_qbr.update_layout(
            paper_bgcolor="#161b22", plot_bgcolor="#161b22",
            font_color="#c9d1d9",
            height=280,
            margin=dict(l=0, r=0, t=10, b=10),
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(autorange="reversed"),
        )
        fig_qbr.update_traces(textfont_color="#fff", textposition="outside")
        st.plotly_chart(fig_qbr, use_container_width=True)
    else:
        st.info("Sin datos de quiebres")

with col4:
    # Detalle de quiebres
    if qbr_rows:
        detalle = []
        for r in qbr_rows:
            pn = clean_player(r.get("Player", "")) or "Sin ID"
            tipo = "Fija" if get_int(r.get("Fija",0)) else ("Móvil" if get_int(r.get("Movil",0)) else "Libre")
            resultado = "Marca Puntos 🏆" if get_int(r.get("Marca puntos",0)) else (
                        "Conecta 🔗"     if get_int(r.get("Conecta compañero",0)) else (
                        "Mantiene 🔒"    if get_int(r.get("Mantiene posesión",0)) else "Pierde ❌"))
            detalle.append({"Jugador": pn, "Tipo": tipo, "Resultado": resultado})
        df_det = pd.DataFrame(detalle)
        st.dataframe(df_det, use_container_width=True, hide_index=True, height=250)

# ── KICKS ──
st.markdown('<div class="section-header">🦵 Kicks por Jugador</div>', unsafe_allow_html=True)

col5, col6 = st.columns([3, 2])
with col5:
    fig_kck = px.bar(
        df_kck,
        x="Jugador",
        y=["Gana Terreno", "Territorial"],
        barmode="group",
        color_discrete_map={"Gana Terreno": "#3fb950", "Territorial": "#58a6ff"},
        text_auto=True,
    )
    fig_kck.update_layout(
        paper_bgcolor="#161b22", plot_bgcolor="#161b22",
        font_color="#c9d1d9",
        height=320,
        margin=dict(l=0, r=0, t=10, b=10),
        legend=dict(font=dict(color="#8b949e"), orientation="h", y=1.1),
        xaxis=dict(gridcolor="#21262d"),
        yaxis=dict(gridcolor="#21262d"),
    )
    st.plotly_chart(fig_kck, use_container_width=True)

with col6:
    st.dataframe(
        df_kck[["Jugador","Total Kicks","Gana Terreno","Territorial","% Efectividad"]],
        use_container_width=True,
        hide_index=True,
    )

# ── PESCA ──
st.markdown('<div class="section-header">🎣 Pesca (Restart Contest)</div>', unsafe_allow_html=True)

col7, col8, col9 = st.columns(3)
with col7:
    pct_pesca_rec = pct_l(pesca_recupera, pesca_nosotros)
    st.markdown(f"""
    <div class="kpi-grid" style="flex-direction:column; gap:12px">
        <div class="kpi-card">
            <div class="kpi-value">{pesca_nosotros}</div>
            <div class="kpi-label">Pesquemos (Nosotros)</div>
            <div class="kpi-sub">{pesca_recupera} recuperadas · {pct_pesca_rec}%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value" style="color:#f85149">{pesca_rival}</div>
            <div class="kpi-label">Pesca del Rival</div>
            <div class="kpi-sub">Salidas rivales ganadas</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value" style="color:#e3b341">{pesca_penal_u}</div>
            <div class="kpi-label">Penales a favor (Pesca)</div>
            <div class="kpi-sub">Infracciones del rival</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col8:
    if not df_psc.empty:
        fig_psc = px.bar(
            df_psc, x="Total", y="Jugador", orientation="h",
            color="Recupera",
            color_continuous_scale=["#1f6feb", "#3fb950"],
            text="Total",
            labels={"Total": "Pescas", "Jugador": ""},
        )
        fig_psc.update_layout(
            paper_bgcolor="#161b22", plot_bgcolor="#161b22",
            font_color="#c9d1d9", height=240,
            margin=dict(l=0, r=0, t=10, b=10),
            coloraxis_colorbar=dict(title="Recup.", tickfont=dict(color="#8b949e")),
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(autorange="reversed"),
        )
        fig_psc.update_traces(textfont_color="#fff", textposition="outside")
        st.plotly_chart(fig_psc, use_container_width=True)
    else:
        st.info("Sin datos de pesca")

with col9:
    if not df_psc.empty:
        st.dataframe(df_psc, use_container_width=True, hide_index=True)

# ── PENALES ──
st.markdown('<div class="section-header">🟡 Penales y Free Kicks</div>', unsafe_allow_html=True)

col10, col11, col12 = st.columns([1, 2, 2])
with col10:
    # Donut para/contra
    fig_pnl_donut = go.Figure(go.Pie(
        labels=["A favor (U)", "En contra"],
        values=[pnl_u, pnl_rival],
        hole=0.6,
        marker_colors=["#3fb950", "#f85149"],
        textinfo="value+percent",
        textfont_size=13,
    ))
    fig_pnl_donut.add_annotation(
        text=f"{pnl_total}<br><span style='font-size:12px'>total</span>",
        font=dict(size=22, color="#f0f6fc", family="Inter"),
        showarrow=False
    )
    fig_pnl_donut.update_layout(
        paper_bgcolor="#161b22", plot_bgcolor="#161b22",
        font_color="#c9d1d9", height=240,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(font=dict(color="#8b949e"), orientation="h", y=-0.1),
        title=dict(text=f"{NAME_LOCAL} vs {NAME_RIVAL}", font=dict(color="#8b949e", size=12), x=0.5),
    )
    st.plotly_chart(fig_pnl_donut, use_container_width=True)

with col11:
    if not df_causas.empty:
        fig_causas = px.bar(
            df_causas, x="Total", y="Causa", orientation="h",
            color="Total",
            color_continuous_scale=["#e3b341", "#f85149"],
            text="Total",
            labels={"Total": "Penales", "Causa": ""},
        )
        fig_causas.update_layout(
            paper_bgcolor="#161b22", plot_bgcolor="#161b22",
            font_color="#c9d1d9", height=280,
            margin=dict(l=0, r=0, t=10, b=10),
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(autorange="reversed"),
            title=dict(text="Causas de Penales", font=dict(color="#8b949e", size=12), x=0.5),
        )
        fig_causas.update_traces(textfont_color="#fff", textposition="outside")
        st.plotly_chart(fig_causas, use_container_width=True)
    else:
        st.info("Sin causas registradas")

with col12:
    if not df_pnl_jug.empty:
        fig_pnl_jug = px.bar(
            df_pnl_jug, x="Penales Cometidos", y="Jugador", orientation="h",
            color="Penales Cometidos",
            color_continuous_scale=["#1f6feb", "#f85149"],
            text="Penales Cometidos",
            labels={"Penales Cometidos": "N°", "Jugador": ""},
        )
        fig_pnl_jug.update_layout(
            paper_bgcolor="#161b22", plot_bgcolor="#161b22",
            font_color="#c9d1d9", height=280,
            margin=dict(l=0, r=0, t=10, b=10),
            showlegend=False, coloraxis_showscale=False,
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(autorange="reversed"),
            title=dict(text="Penales Cometidos por Jugador", font=dict(color="#8b949e", size=12), x=0.5),
        )
        fig_pnl_jug.update_traces(textfont_color="#fff", textposition="outside")
        st.plotly_chart(fig_pnl_jug, use_container_width=True)
    else:
        st.info("Sin datos por jugador")

# ── LINE ──
st.markdown('<div class="section-header">📏 Line Out</div>', unsafe_allow_html=True)

col13, col14 = st.columns(2)

with col13:
    # Line propias
    pct_limpia = pct_l(lin_limpia_prop, lin_total_prop)
    pct_perd   = pct_l(lin_perdida_prop, lin_total_prop)
    pct_rob    = pct_l(lin_robada_prop, lin_total_prop)
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin-bottom:12px">
        <div style="font-size:0.85rem;color:#58a6ff;font-weight:700;margin-bottom:12px;text-transform:uppercase">🔵 Lines Propias ({lin_total_prop})</div>
        <table style="width:100%;border-collapse:collapse;color:#c9d1d9;font-size:0.9rem">
          <tr>
            <td style="padding:6px 0">✅ Pelota Limpia</td>
            <td style="text-align:right;font-weight:700;color:#3fb950">{lin_limpia_prop} / {lin_total_prop}</td>
            <td style="text-align:right;color:#8b949e;padding-left:12px">{pct_limpia}%</td>
          </tr>
          <tr>
            <td style="padding:6px 0">❌ Perdida</td>
            <td style="text-align:right;font-weight:700;color:#f85149">{lin_perdida_prop} / {lin_total_prop}</td>
            <td style="text-align:right;color:#8b949e;padding-left:12px">{pct_perd}%</td>
          </tr>
          <tr>
            <td style="padding:6px 0">🔄 Robada por Rival</td>
            <td style="text-align:right;font-weight:700;color:#e3b341">{lin_robada_prop} / {lin_total_prop}</td>
            <td style="text-align:right;color:#8b949e;padding-left:12px">{pct_rob}%</td>
          </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # Barchart propias
    df_lin_prop = pd.DataFrame([
        {"Resultado": "Pelota Limpia", "n": lin_limpia_prop},
        {"Resultado": "Perdida",       "n": lin_perdida_prop},
        {"Resultado": "Robada",        "n": lin_robada_prop},
    ])
    fig_lin = px.bar(
        df_lin_prop, x="Resultado", y="n",
        color="Resultado",
        color_discrete_map={"Pelota Limpia": "#3fb950", "Perdida": "#f85149", "Robada": "#e3b341"},
        text="n",
    )
    fig_lin.update_layout(
        paper_bgcolor="#161b22", plot_bgcolor="#161b22",
        font_color="#c9d1d9", height=220,
        margin=dict(l=0, r=0, t=10, b=10),
        showlegend=False,
        yaxis=dict(gridcolor="#21262d"),
    )
    fig_lin.update_traces(textfont_color="#fff", textposition="outside")
    st.plotly_chart(fig_lin, use_container_width=True)

with col14:
    # Line rival
    pct_limpia_r = pct_l(lin_limpia_riv, lin_total_riv)
    pct_rob_r    = pct_l(lin_robada_riv, lin_total_riv)
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin-bottom:12px">
        <div style="font-size:0.85rem;color:#f85149;font-weight:700;margin-bottom:12px;text-transform:uppercase">🔴 Lines Rivales ({lin_total_riv})</div>
        <table style="width:100%;border-collapse:collapse;color:#c9d1d9;font-size:0.9rem">
          <tr>
            <td style="padding:6px 0">✅ Pelota Limpia (Rival)</td>
            <td style="text-align:right;font-weight:700;color:#f85149">{lin_limpia_riv} / {lin_total_riv}</td>
            <td style="text-align:right;color:#8b949e;padding-left:12px">{pct_limpia_r}%</td>
          </tr>
          <tr>
            <td style="padding:6px 0">🔄 Robadas por Nosotros</td>
            <td style="text-align:right;font-weight:700;color:#3fb950">{lin_robada_riv} / {lin_total_riv}</td>
            <td style="text-align:right;color:#8b949e;padding-left:12px">{pct_rob_r}%</td>
          </tr>
          <tr>
            <td style="padding:6px 0">❌ Perdidas (Rival)</td>
            <td style="text-align:right;font-weight:700;color:#e3b341">{lin_perdida_riv} / {lin_total_riv}</td>
            <td style="text-align:right;color:#8b949e;padding-left:12px">{pct_l(lin_perdida_riv, lin_total_riv)}%</td>
          </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # Barchart rival
    df_lin_riv = pd.DataFrame([
        {"Resultado": "Limpia (Rival)",  "n": lin_limpia_riv},
        {"Resultado": "Robada por CULP", "n": lin_robada_riv},
        {"Resultado": "Perdida (Rival)", "n": lin_perdida_riv},
    ])
    fig_lin_r = px.bar(
        df_lin_riv, x="Resultado", y="n",
        color="Resultado",
        color_discrete_map={"Limpia (Rival)": "#f85149", "Robada por CULP": "#3fb950", "Perdida (Rival)": "#e3b341"},
        text="n",
    )
    fig_lin_r.update_layout(
        paper_bgcolor="#161b22", plot_bgcolor="#161b22",
        font_color="#c9d1d9", height=220,
        margin=dict(l=0, r=0, t=10, b=10),
        showlegend=False,
        yaxis=dict(gridcolor="#21262d"),
    )
    fig_lin_r.update_traces(textfont_color="#fff", textposition="outside")
    st.plotly_chart(fig_lin_r, use_container_width=True)

# ── FOOTER ──
st.markdown("""
<div style="text-align:center; color:#484f58; font-size:0.78rem; margin-top:40px; padding:16px; border-top:1px solid #21262d">
    Club Universitario de La Plata · Sistema de Análisis de Rendimiento · Primera A 2026
</div>
""", unsafe_allow_html=True)
