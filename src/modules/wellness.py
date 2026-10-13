import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.sheets.google_sheets_manager import get_sheets_manager

def calculate_wellness_score(rpe, sueno, doms):
    # Normalizamos el RPE (1-10) a una escala de 1-5
    rpe_ajustado_norm = (11 - rpe) / 2
    doms_ajustado = 6 - doms 
    score = (sueno + doms_ajustado + rpe_ajustado_norm) / 3
    return round(score, 2)

def get_status_color(score):
    if score >= 4: return "#28a745" # Verde
    elif score >= 3: return "#ffc107" # Amarillo
    else: return "#dc3545" # Rojo

def get_emoji_for_val(val, key):
    if key == "rpe":
        if val <= 3: return "🟢"
        if val <= 6: return "🟡"
        return "🔴"
    elif key == "doms":
        if val <= 1: return "🟢"
        if val <= 3: return "🟡"
        return "🔴"
    else:
        if val <= 2: return "🔴"
        if val <= 3: return "🟡"
        return "🟢"

def _hero(titulo, sub):
    st.markdown(f"""
    <div class="well-hero"><h1>{titulo}</h1><p>{sub}</p></div>
    """, unsafe_allow_html=True)


def _estado_chip(label, val, key, ayuda):
    emoji = get_emoji_for_val(val, key)
    return (f'<div class="well-chip"><span class="well-chip-l">{label}</span>'
            f'<span class="well-chip-v">{emoji} {val}</span>'
            f'<span class="well-chip-h">{ayuda}</span></div>')


WELL_CSS = """
<style>
.well-hero { background: linear-gradient(135deg,#000 0%,#212529 100%); border:2px solid rgba(255,255,255,0.1);
  border-radius:20px; padding:clamp(1rem,4vw,1.6rem); text-align:center; margin-bottom:1rem; box-shadow:0 10px 25px rgba(0,0,0,0.35); }
.well-hero h1 { color:#fff !important; margin:0; font-size:clamp(1.25rem,6vw,2rem); font-weight:800; letter-spacing:1px; text-transform:uppercase; }
.well-hero p { color:#E0E0E0; margin:.4rem 0 0 0; font-size:clamp(.85rem,3.5vw,1rem); font-weight:300; }
.well-card { background: linear-gradient(135deg,#111 0%,#2a2d31 100%); border-radius:16px; padding:.9rem 1.1rem; margin:.4rem 0 .8rem 0;
  border-left:5px solid #28a745; }
.well-card h3 { margin:0; color:#fff !important; font-size:1.05rem; text-transform:uppercase; letter-spacing:.5px; }
.well-card p { margin:.2rem 0 0 0; color:#bbb; font-size:.85rem; }
.well-chips { display:flex; gap:.5rem; margin:.3rem 0 1rem 0; }
.well-chip { flex:1; background:#f4f5f7; border-radius:14px; padding:.55rem .3rem; text-align:center; min-width:0; }
.well-chip-l { display:block; font-size:.68rem; color:#666; text-transform:uppercase; font-weight:700; }
.well-chip-v { display:block; font-size:1.25rem; font-weight:800; color:#111; }
.well-chip-h { display:block; font-size:.68rem; color:#888; }
.well-empty { background:rgba(0,0,0,0.04); border-radius:14px; padding:1rem; text-align:center; color:#666; font-size:.9rem; }
.well-score { background:linear-gradient(135deg,#000,#212529); color:#fff; border-radius:16px; padding:1rem; text-align:center; margin-top:.6rem; }
.well-score b { font-size:2rem; display:block; }
div[data-baseweb="select"] > div { min-height: 48px; }
.stButton > button { min-height: 52px; font-weight:700; letter-spacing:.5px; border-radius:14px; }
[data-testid="stSlider"] { padding: .2rem .6rem; }
[data-testid="stSlider"] [role="slider"] { width: 28px; height: 28px; }
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.25rem !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
    [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: 100% !important; flex: 1 1 100% !important; }
}
</style>
"""


@st.cache_data(ttl=300, show_spinner=False)
def _leer_wellness(sheet_id, _gsm):
    ws = _gsm.client.open_by_key(sheet_id).worksheet("Wellness_Jugador")
    return pd.DataFrame(ws.get_all_records())


@st.cache_data(ttl=300, show_spinner=False)
def _leer_maestro(sheet_id, _gsm):
    ws = _gsm.client.open_by_key(sheet_id).worksheet("Jugadores_Maestro")
    return pd.DataFrame(ws.get_all_records())


def wellness_module():
    st.markdown(WELL_CSS, unsafe_allow_html=True)
    _hero("📝 Wellness", "Contanos cómo estás hoy · 30 segundos")

    gsm = get_sheets_manager()
    if not gsm.sheet_config.get("sheet_id"):
        gsm.sheet_config["sheet_id"] = "1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw"

    user = st.session_state.user
    is_staff = user.get('rol') in ['Administrador', 'Entrenador', 'Preparador Físico']

    # --- PESTAÑAS SEGÚN ROL ---
    if is_staff:
        tab1, tab2 = st.tabs(["📋 Mi Registro / Prueba", "👥 Panel de Equipo (Staff)"])
    else:
        tab1 = st.container() # El jugador solo ve su parte

    with tab1:
        # --- FORMULARIO DE ENTRADA ---
        with st.container():
            st.markdown("""
            <div class='well-card'>
                <h3>Registro diario</h3>
                <p>Deslizá cada barra y enviá.</p>
            </div>
            """, unsafe_allow_html=True)

            rpe = st.slider("Esfuerzo del día (RPE) · 1 suave, 10 máximo", 1, 10, 5, key="rpe_sel")
            sueno = st.slider("Calidad de sueño · 1 mala, 5 excelente", 1, 5, 5, key="sueno_sel")
            doms = st.slider("Dolor muscular (DOMS) · 1 nada, 5 mucho", 1, 5, 1, key="doms_sel")

            st.markdown('<div class="well-chips">'
                        + _estado_chip("Esfuerzo", rpe, "rpe", "de 10")
                        + _estado_chip("Sueño", sueno, "sueno", "de 5")
                        + _estado_chip("Dolor", doms, "doms", "de 5")
                        + '</div>', unsafe_allow_html=True)

            if st.button("🚀 ENVIAR", use_container_width=True, type="primary"):
                score = calculate_wellness_score(rpe, sueno, doms)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                fecha = datetime.now().strftime("%Y-%m-%d")
                try:
                    spreadsheet = gsm.client.open_by_key(gsm.sheet_config["sheet_id"])
                    worksheet = spreadsheet.worksheet("Wellness_Jugador")
                    row = [len(worksheet.col_values(1)), timestamp, user.get('email', 'N/A'), user['nombre'], rpe, sueno, doms, score, fecha]
                    worksheet.append_row(row)
                    _leer_wellness.clear()
                    st.markdown(f"<div class='well-score'>✅ ¡Enviado!<b style='color:{get_status_color(score)}'>{score}</b>Tu score de hoy (de 5)</div>", unsafe_allow_html=True)
                except Exception:
                    st.warning("No pudimos guardar tu registro ahora. Revisá tu conexión e intentá de nuevo en un momento.")

        # --- HISTORIAL PERSONAL ---
        st.markdown("<div class='well-card' style='border-left-color:#fff'><h3>📊 Tu evolución</h3></div>", unsafe_allow_html=True)
        shown = False
        try:
            df = _leer_wellness(gsm.sheet_config["sheet_id"], gsm)
            if not df.empty:
                df_p = df[df['Nombre_Jugador'] == user['nombre']]
                if not df_p.empty:
                    df_p = df_p.copy()
                    df_p['Fecha'] = pd.to_datetime(df_p['Fecha'])
                    fig = go.Figure(go.Scatter(x=df_p['Fecha'], y=df_p['Wellness_Score'], mode='lines+markers', line=dict(color='black')))
                    fig.update_layout(height=240, margin=dict(l=0,r=0,t=10,b=0), yaxis=dict(range=[1,5.2]), xaxis=dict(tickformat='%d/%m', nticks=4))
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    shown = True
            if not shown:
                st.markdown("<div class='well-empty'>Todavía no tenés registros. Enviá el primero y vas a ver tu evolución acá.</div>", unsafe_allow_html=True)
        except Exception:
            st.markdown("<div class='well-empty'>Tu evolución no está disponible en este momento.</div>", unsafe_allow_html=True)

    # --- PANEL PARA ENTRENADORES ---
    if is_staff:
        with tab2:
            st.markdown("<div class='well-card'><h3>🏁 Semáforo por categoría</h3></div>", unsafe_allow_html=True)
            try:
                df_master = _leer_maestro(gsm.sheet_config["sheet_id"], gsm)
                df_well = _leer_wellness(gsm.sheet_config["sheet_id"], gsm)
                
                if not df_master.empty:
                    categorias = sorted(df_master['Division'].unique())
                    cat_sel = st.selectbox("Seleccionar Categoría", options=categorias)
                    
                    # Filtrar jugadores de esa categoría
                    jugadores_cat = df_master[df_master['Division'] == cat_sel]
                    
                    # Obtener último wellness de cada uno
                    results = []
                    for _, player in jugadores_cat.iterrows():
                        p_name = f"{player['Nombre']} {player['Apellido']}".strip()
                        # Buscar último registro en wellness
                        p_well = df_well[df_well['Nombre_Jugador'] == p_name].sort_values('Timestamp').tail(1)
                        
                        score = "N/A"
                        color = "⚪"
                        if not p_well.empty:
                            score = p_well.iloc[0]['Wellness_Score']
                            color = "🟢" if score >= 4 else ("🟡" if score >= 3 else "🔴")
                        
                        results.append({
                            "Estado": color,
                            "Jugador": p_name,
                            "Último Score": score,
                            "Fecha": p_well.iloc[0]['Fecha'] if not p_well.empty else "-"
                        })
                    
                    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
                    
                    st.info("💡 Consejo: Los jugadores en 🔴 no deberían realizar tareas de máxima intensidad hoy.")
                else:
                    st.warning("No hay jugadores cargados en la base de datos.")
            except Exception as e:
                st.warning("No se pudo cargar el panel del equipo ahora. Probá de nuevo en un momento.")
