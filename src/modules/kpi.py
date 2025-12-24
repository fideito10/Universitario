import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def main_kpi():
    # Configuración de la página y estilos (si se ejecuta standalone, aunque probablemente sea un módulo)
    # Si es módulo, heredará estilos, pero aseguramos consistencia.
    
    st.markdown("""
    <style>
        .kpi-card {
            background-color: #1E1E1E;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #333;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .kpi-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #ffffff;
        }
        .kpi-label {
            font-size: 1rem;
            color: #aaaaaa;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stHeader {
            background-color: transparent;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("🏉 Panel de Alto Rendimiento - KPI Pantera")
    st.markdown("### Análisis de Rendimiento y Factores Clave de Victoria")

    # --- 1. Gestión de Datos (Simulada por ahora, idealmente Google Sheets/DB) ---
    if 'match_data' not in st.session_state:
        # Datos iniciales de ejemplo
        st.session_state.match_data = pd.DataFrame([
            {"Rival": "Los Tilos", "Fecha": "2024-03-15", "Resultado": "G", "Puntos_Favor": 28, "Puntos_Contra": 15, "Tackles_Hechos": 145, "Tackles_Errados": 12, "Entradas_22m": 8, "Puntos_en_22m": 21, "Scrum_Ganados": 8, "Scrum_Perdidos": 1, "Line_Ganados": 12, "Line_Perdidos": 2, "Penales_Cometidos": 8},
            {"Rival": "San Luis", "Fecha": "2024-03-22", "Resultado": "P", "Puntos_Favor": 14, "Puntos_Contra": 20, "Tackles_Hechos": 110, "Tackles_Errados": 25, "Entradas_22m": 5, "Puntos_en_22m": 7, "Scrum_Ganados": 6, "Scrum_Perdidos": 2, "Line_Ganados": 10, "Line_Perdidos": 4, "Penales_Cometidos": 14},
            {"Rival": "La Plata", "Fecha": "2024-03-29", "Resultado": "G", "Puntos_Favor": 35, "Puntos_Contra": 10, "Tackles_Hechos": 160, "Tackles_Errados": 8, "Entradas_22m": 10, "Puntos_en_22m": 28, "Scrum_Ganados": 9, "Scrum_Perdidos": 0, "Line_Ganados": 14, "Line_Perdidos": 1, "Penales_Cometidos": 6},
        ])

    df = st.session_state.match_data

    # --- 2. Sidebar: Carga de Nuevo Partido ---
    with st.sidebar:
        st.header("📝 Cargar Nuevo Partido")
        with st.form("new_match_form"):
            rival = st.text_input("Rival")
            fecha = st.date_input("Fecha")
            resultado = st.selectbox("Resultado", ["G", "P", "E"])
            
            col1, col2 = st.columns(2)
            p_favor = col1.number_input("Puntos a Favor", min_value=0)
            p_contra = col2.number_input("Puntos en Contra", min_value=0)
            
            st.subheader("🛡️ Defensa")
            tackles_ok = st.number_input("Tackles Hechos", min_value=0)
            tackles_miss = st.number_input("Tackles Errados", min_value=0)
            
            st.subheader("⚔️ Ataque (Zona Roja)")
            entradas_22 = st.number_input("Entradas a 22m", min_value=0)
            puntos_22 = st.number_input("Puntos anotados tras entrar a 22m", min_value=0)
            
            st.subheader("🏗️ Obtención y Disciplina")
            scrum_ok = st.number_input("Scrums Propios Ganados", min_value=0)
            scrum_lost = st.number_input("Scrums Propios Perdidos", min_value=0)
            line_ok = st.number_input("Lines Propios Ganados", min_value=0)
            line_lost = st.number_input("Lines Propios Perdidos", min_value=0)
            penales = st.number_input("Penales Cometidos", min_value=0)
            
            submit = st.form_submit_button("Guardar Partido")
            
            if submit:
                new_data = {
                    "Rival": rival, "Fecha": str(fecha), "Resultado": resultado,
                    "Puntos_Favor": p_favor, "Puntos_Contra": p_contra,
                    "Tackles_Hechos": tackles_ok, "Tackles_Errados": tackles_miss,
                    "Entradas_22m": entradas_22, "Puntos_en_22m": puntos_22,
                    "Scrum_Ganados": scrum_ok, "Scrum_Perdidos": scrum_lost,
                    "Line_Ganados": line_ok, "Line_Perdidos": line_lost,
                    "Penales_Cometidos": penales
                }
                st.session_state.match_data = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                st.success("Partido guardado exitosamente!")
                st.rerun()

    # --- 3. Cálculos de KPIs Avanzados ---
    # Efectividad de Tackle
    df['Efectividad_Tackle'] = (df['Tackles_Hechos'] / (df['Tackles_Hechos'] + df['Tackles_Errados']) * 100).fillna(0)
    # Eficiencia en 22m (Puntos por entrada)
    df['Eficiencia_22m'] = (df['Puntos_en_22m'] / df['Entradas_22m']).fillna(0)
    # Obtención (Scrum + Line)
    df['Efectividad_Scrum'] = (df['Scrum_Ganados'] / (df['Scrum_Ganados'] + df['Scrum_Perdidos']) * 100).fillna(0)
    df['Efectividad_Line'] = (df['Line_Ganados'] / (df['Line_Ganados'] + df['Line_Perdidos']) * 100).fillna(0)

    # --- 4. Dashboard Principal ---
    
    # KPIs Globales (Promedios)
    st.markdown("### 📊 Resumen de Temporada")
    col1, col2, col3, col4 = st.columns(4)
    
    avg_tackle = df['Efectividad_Tackle'].mean()
    avg_eff_22 = df['Eficiencia_22m'].mean()
    avg_penalties = df['Penales_Cometidos'].mean()
    win_rate = (df[df['Resultado'] == 'G'].shape[0] / df.shape[0] * 100) if df.shape[0] > 0 else 0

    col1.metric("Efectividad Tackle", f"{avg_tackle:.1f}%")
    col2.metric("Puntos por Entrada a 22m", f"{avg_eff_22:.1f}")
    col3.metric("Penales Promedio", f"{avg_penalties:.1f}", delta=-avg_penalties, delta_color="inverse") 
    col4.metric("Win Rate", f"{win_rate:.0f}%")

    st.markdown("---")

    # --- 5. Visualizaciones Detalladas (Todo en un panel) ---
    
    # Fila 1: Defensa y Ataque
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.markdown("#### 🛡️ La Muralla (Tackles)")
        # Gráfico de barras apiladas: Tackles Hechos vs Errados
        # Colores: Hechos (Blanco/Gris Claro), Errados (Gris Oscuro/Negro)
        fig_tackles = go.Figure(data=[
            go.Bar(name='Hechos', x=df['Rival'], y=df['Tackles_Hechos'], marker_color='#ffffff'),
            go.Bar(name='Errados', x=df['Rival'], y=df['Tackles_Errados'], marker_color='#444444')
        ])
        fig_tackles.update_layout(
            barmode='stack', 
            title="Volumen de Tackles", 
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_tackles, use_container_width=True)

    with row1_col2:
        st.markdown("#### ⚔️ Zona Roja (22m)")
        # Gráfico de doble eje
        fig_22 = go.Figure()
        fig_22.add_trace(go.Bar(x=df['Rival'], y=df['Entradas_22m'], name='Entradas', marker_color='#888888'))
        fig_22.add_trace(go.Scatter(x=df['Rival'], y=df['Puntos_en_22m'], name='Puntos', yaxis='y2', line=dict(color='#ffffff', width=3)))
        
        fig_22.update_layout(
            title="Eficiencia en 22m",
            yaxis=dict(title="Entradas"),
            yaxis2=dict(title="Puntos", overlaying='y', side='right'),
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_22, use_container_width=True)

    st.markdown("---")

    # Fila 2: Obtención y Disciplina
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.markdown("#### 🏗️ Plataforma de Juego")
        if not df.empty:
            last_match = df.iloc[-1]
            # Radar chart
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=[last_match['Efectividad_Scrum'], last_match['Efectividad_Line'], last_match['Efectividad_Tackle'], (last_match['Puntos_Favor']/(last_match['Puntos_Favor']+last_match['Puntos_Contra']+0.1))*100],
                theta=['Scrum %', 'Line %', 'Tackle %', 'Dominio %'],
                fill='toself',
                name=last_match['Rival'],
                line_color='#ffffff',
                fillcolor='rgba(255, 255, 255, 0.3)'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
                title=f"Perfil vs {last_match['Rival']}", 
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_radar, use_container_width=True)

    with row2_col2:
        st.markdown("#### ⚠️ Disciplina")
        # Evolución de Penales
        fig_penales = px.line(df, x='Rival', y='Penales_Cometidos', markers=True, title="Penales Cometidos")
        fig_penales.update_traces(line_color='#ffffff', marker_color='#ffffff')
        fig_penales.add_hline(y=10, line_dash="dash", line_color="#888888", annotation_text="Límite (10)")
        fig_penales.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_penales, use_container_width=True)

    # Tabla de Datos Crudos
    with st.expander("Ver Planilla de Datos"):
        st.dataframe(df.style.highlight_max(axis=0, color='#333333'))

if __name__ == "__main__":
    main_kpi()
