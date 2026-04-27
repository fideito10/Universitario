import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.sheets.google_sheets_manager import GoogleSheetsManager

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

def wellness_module():
    st.markdown('<div class="main-header"><h1>📝 Wellness del Jugador</h1><p>Monitoreo de carga y recuperación</p></div>', unsafe_allow_html=True)
    
    gsm = GoogleSheetsManager()
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
            <div style='background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 1rem;'>
                <h3 style='margin-top:0; color:#111;'>Registro Diario</h3>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                rpe_options = [f"{get_emoji_for_val(i, 'rpe')} {i}" for i in range(1, 11)]
                rpe_sel = st.selectbox("Esfuerzo (RPE)", options=rpe_options, index=4, key="rpe_sel")
                rpe = int(rpe_sel.split()[-1])
            with c2:
                sueno_options = [f"{get_emoji_for_val(i, 'sueno')} {i}" for i in range(1, 6)]
                sueno_sel = st.selectbox("Calidad de Sueño", options=sueno_options, index=4, key="sueno_sel")
                sueno = int(sueno_sel.split()[-1])
            with c3:
                doms_options = [f"{get_emoji_for_val(i, 'doms')} {i}" for i in range(1, 6)]
                doms_sel = st.selectbox("Dolor Muscular (DOMS)", options=doms_options, index=0, key="doms_sel")
                doms = int(doms_sel.split()[-1])
                
            if st.button("🚀 ENVIAR PERCEPCIÓN", use_container_width=True, type="primary"):
                score = calculate_wellness_score(rpe, sueno, doms)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                fecha = datetime.now().strftime("%Y-%m-%d")
                try:
                    spreadsheet = gsm.client.open_by_key(gsm.sheet_config["sheet_id"])
                    worksheet = spreadsheet.worksheet("Wellness_Jugador")
                    row = [len(worksheet.get_all_values()), timestamp, user.get('email', 'N/A'), user['nombre'], rpe, sueno, doms, score, fecha]
                    worksheet.append_row(row)
                    st.success(f"✅ ¡Enviado! Score: {score}")
                except Exception as e:
                    st.error(f"Error: {e}")

        # --- HISTORIAL PERSONAL ---
        st.markdown("---")
        st.subheader("📊 Tu Evolución")
        try:
            spreadsheet = gsm.client.open_by_key(gsm.sheet_config["sheet_id"])
            ws_wellness = spreadsheet.worksheet("Wellness_Jugador")
            df = pd.DataFrame(ws_wellness.get_all_records())
            if not df.empty:
                df_p = df[df['Nombre_Jugador'] == user['nombre']]
                if not df_p.empty:
                    df_p['Fecha'] = pd.to_datetime(df_p['Fecha'])
                    fig = go.Figure(go.Scatter(x=df_p['Fecha'], y=df_p['Wellness_Score'], mode='lines+markers', line=dict(color='black')))
                    fig.update_layout(height=250, margin=dict(l=0,r=0,t=10,b=0), yaxis=dict(range=[1,5.2]))
                    st.plotly_chart(fig, use_container_width=True)
        except: pass

    # --- PANEL PARA ENTRENADORES ---
    if is_staff:
        with tab2:
            st.subheader("🏁 Semáforo de Bienestar por Categoría")
            try:
                spreadsheet = gsm.client.open_by_key(gsm.sheet_config["sheet_id"])
                ws_master = spreadsheet.worksheet("Jugadores_Maestro")
                ws_well = spreadsheet.worksheet("Wellness_Jugador")
                
                df_master = pd.DataFrame(ws_master.get_all_records())
                df_well = pd.DataFrame(ws_well.get_all_records())
                
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
                    
                    st.table(pd.DataFrame(results))
                    
                    st.info("💡 Consejo: Los jugadores en 🔴 no deberían realizar tareas de máxima intensidad hoy.")
                else:
                    st.warning("No hay jugadores cargados en la base de datos.")
            except Exception as e:
                st.error(f"Error cargando el panel: {e}")
