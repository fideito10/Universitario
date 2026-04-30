import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
from src.sheets.google_sheets_manager import GoogleSheetsManager

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def fetch_rugby_data():
    gsm = GoogleSheetsManager()
    sheet_id = "1hYAD7j4DIibW37hVyB7fAVOl_dzoMcg-cHJaP6MX2jo"
    
    try:
        ss = gsm.client.open_by_key(sheet_id)
        
        # Acciones Acumuladas
        ws_acum = ss.worksheet("Acciones Acumuladas")
        data_acum = ws_acum.get_all_values()
        df_acum = pd.DataFrame(data_acum[1:], columns=[str(h).strip() for h in data_acum[0]])
        
        # Intensidad
        ws_int = ss.worksheet("Intensidad Indv.")
        data_int = ws_int.get_all_values()
        header_idx = 0
        for i, row in enumerate(data_int):
            if "Nombre" in row:
                header_idx = i
                break
        df_int = pd.DataFrame(data_int[header_idx+1:], columns=[str(h).strip() for h in data_int[header_idx]])
        
        # Normalización de Columnas
        for col in df_acum.columns:
            if 'RUCK' in col.upper():
                df_acum = df_acum.rename(columns={col: 'RUCK'})
        
        rename_map = {
            'Nombre': 'JUGADOR', 
            'NF /INTENS,': 'EFICIENCIA',
            'Intensidad': 'INTENS.'
        }
        df_acum = df_acum.rename(columns=rename_map)
        df_int = df_int.rename(columns=rename_map)
        
        # Mapeo de Partidos
        match_mapping = {
            '14/3/2026': 'vs. Hurling (F1)',
            '21/3/2026': 'vs. San Andres (F2)',
            '28/3/2026': 'vs. Pucará (F3)',
            '11/4/2026': 'vs. Pueyrredón (F4)',
            '18/4/2026': 'vs. San Fernando (F5)',
            '25/4/2026': 'vs. Dep. Francesa (F6)'
        }
        df_acum['Partido'] = df_acum['Fecha'].map(match_mapping).fillna(df_acum['Fecha'])
        
        cols_ignore = ['JUGADOR', 'Fecha', 'Partido', 'CHK FECHA', 'CHK NOMBRE']
        for df in [df_acum, df_int]:
            if not df.empty and 'JUGADOR' in df.columns:
                df['JUGADOR'] = df['JUGADOR'].astype(str).str.strip()
                df.drop(df[df['JUGADOR'] == ''].index, inplace=True)
                for col in df.columns:
                    if col not in cols_ignore:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        return df_acum, df_int, match_mapping
    except Exception as e:
        st.error(f"Error de datos: {e}")
        return None, None, {}

def rugby_analysis_module():
    logo_b64 = get_base64_image("escudo uni.jpg")
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        .stApp {{ background-color: #000000; color: #FFFFFF; font-family: 'Inter', sans-serif; }}
        .main-header-uni {{ background: linear-gradient(135deg, #000000 0%, #121212 100%); padding: 3rem; border-radius: 20px; border-bottom: 5px solid #FFFFFF; margin-bottom: 2rem; text-align: center; }}
        
        .metric-card-uni {{ background: rgba(255, 255, 255, 0.08); border: 2px solid rgba(255, 255, 255, 0.2); border-radius: 25px; padding: 2.5rem; text-align: center; backdrop-filter: blur(15px); }}
        .metric-val {{ font-size: 5rem; font-weight: 900; color: #FFFFFF; margin: 0; line-height: 1; letter-spacing: -3px; }}
        .metric-label {{ font-size: 1.3rem; font-weight: 700; color: #FFFFFF; text-transform: uppercase; letter-spacing: 3px; margin-top: 0.5rem; }}
        
        .top-player-card {{ background: linear-gradient(180deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.03) 100%); border-radius: 18px; padding: 22px; margin-bottom: 15px; border-left: 8px solid #FFF; }}
        .top-player-name {{ font-size: 1.4rem; font-weight: 900; color: #FFFFFF; text-transform: uppercase; }}
        .top-player-stats {{ font-size: 1.2rem; font-weight: 700; color: #AAAAAA; }}
        
        .section-title {{ font-size: 2.5rem; font-weight: 900; border-left: 10px solid #FFF; padding-left: 25px; margin: 4rem 0 2.5rem 0; text-transform: uppercase; letter-spacing: 4px; }}
        .analyst-box {{ background-color: #050505; border: 2px solid #333; border-radius: 25px; padding: 35px; margin: 45px 0; border-left: 12px solid #FFFFFF; }}
        </style>
        <div class="main-header-uni">
            <img src="data:image/jpeg;base64,{logo_b64}" style="width: 120px;">
            <h1 style='margin: 0; letter-spacing: 5px; font-weight: 900; font-size: 3.5rem;'>PANEL TÁCTICO CULP</h1>
            <p style='opacity: 0.9; font-size: 1.4rem; letter-spacing: 3px; font-weight: 300;'>2026 · ANÁLISIS DE RENDIMIENTO</p>
        </div>
    """, unsafe_allow_html=True)

    df_acum, df_int, match_mapping = fetch_rugby_data()
    if df_acum is None: return

    # Filtros
    partidos = sorted(df_acum['Partido'].unique())
    selected_match = st.selectbox("🏟️ SELECCIONAR PARTIDO", partidos, index=len(partidos)-1)
    df_match = df_acum[df_acum['Partido'] == selected_match]

    tab1, tab2, tab3 = st.tabs(["📊 RENDIMIENTO COLECTIVO", "👤 FICHA JUGADOR", "⚡ INTENSIDAD"])

    cols_stats = [c for c in df_match.columns if c not in ['JUGADOR', 'Fecha', 'Partido', 'MINUTOS', 'CHK FECHA', 'CHK NOMBRE', '5', 'TOTAL']]

    with tab1:
        st.markdown(f"<h2 class='section-title'>BALANCE: {selected_match}</h2>", unsafe_allow_html=True)
        
        # Métricas Globales
        total_team = df_match[cols_stats].sum()
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="metric-card-uni"><p class="metric-val">{int(total_team.get("TACKLE", 0))}</p><p class="metric-label">Tackles</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card-uni"><p class="metric-val">{int(total_team.get("QUIEBRE", 0))}</p><p class="metric-label">Quiebres</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card-uni"><p class="metric-val">{int(total_team.get("PENAL", 0))}</p><p class="metric-label">Penales</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card-uni"><p class="metric-val">{int(total_team.get("NO FORZADO", 0))}</p><p class="metric-label">E. No Forzados</p></div>', unsafe_allow_html=True)

        st.markdown("<h2 class='section-title'>🏆 LÍDERES DEL ENCUENTRO</h2>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        
        def render_top3(column, title, emoji):
            if column not in df_match.columns: return
            top = df_match.sort_values(by=column, ascending=False).head(3)
            with st.container():
                st.markdown(f"<p style='font-size:1.4rem; font-weight:900; letter-spacing:1px;'>{emoji} {title}</p>", unsafe_allow_html=True)
                for i, (idx, row) in enumerate(top.iterrows()):
                    if row[column] > 0:
                        st.markdown(f"""<div class="top-player-card">
                            <span class="top-player-name">{row['JUGADOR']}</span><br>
                            <span class="top-player-stats">{int(row[column])} acciones</span>
                        </div>""", unsafe_allow_html=True)

        with c1: render_top3('TACKLE', 'TACKLES', '🏉')
        with c2: render_top3('QUIEBRE', 'QUIEBRES', '🔥')
        with c3: render_top3('PESCA', 'PESCAS', '🎣')
        with c4: render_top3('RUCK', 'RUCKS', '💪')

        nf_val = int(total_team.get("NO FORZADO", 0))
        st.markdown(f"""<div class="analyst-box">
            <h4 style='color: #FFF; font-weight:900; font-size:1.5rem;'>📝 COMENTARIO PROFESIONAL</h4>
            <p style='color: #CCC; font-size: 1.2rem; line-height:1.6;'>
                El equipo mantuvo un volumen defensivo alto. La clave del próximo encuentro será reducir los <b>{nf_val} Errores No Forzados</b> que están entregando la posesión en campo propio. 
                Los líderes en rucks están garantizando pelotas de calidad, hay que explotar más los quiebres generados en la base.
            </p>
        </div>""", unsafe_allow_html=True)

        st.markdown("<h2 class='section-title'>📊 GRÁFICOS DEMOSTRATIVOS</h2>", unsafe_allow_html=True)
        
        g1, g2 = st.columns(2)
        with g1:
            # Gráfico de Radar de Consistencia del Equipo
            radar_labels = ['Tackles', 'Quiebres', 'Pescas', 'Penales (inv)', 'Err. No Forzados (inv)']
            penal_inv = max(0, 20 - total_team.get('PENAL', 0)) # Invertido para que mas sea mejor en el radar
            nf_inv = max(0, 20 - total_team.get('NO FORZADO', 0))
            radar_vals = [total_team.get('TACKLE', 0)/5, total_team.get('QUIEBRE', 0)*2, total_team.get('PESCA', 0)*2, penal_inv, nf_inv]
            
            fig_radar_team = go.Figure(data=go.Scatterpolar(
                r=radar_vals, theta=radar_labels, fill='toself',
                line_color='#FFFFFF', fillcolor='rgba(255,255,255,0.3)'
            ))
            fig_radar_team.update_layout(polar=dict(radialaxis=dict(visible=False)), showlegend=False, title="RADAR DE CONSISTENCIA TÁCTICA", template='plotly_dark')
            st.plotly_chart(fig_radar_team, use_container_width=True)
        
        with g2:
            # Top 10 Jugadores de Alto Impacto
            df_match['IMPACTO'] = df_match['TACKLE'] + df_match['QUIEBRE'] + df_match['PESCA']
            top10 = df_match.sort_values(by='IMPACTO', ascending=False).head(10)
            
            fig_impacto = px.bar(top10, x='IMPACTO', y='JUGADOR', orientation='h', 
                                title="TOP 10 IMPACTO POSITIVO", template='plotly_dark')
            
            # Estilo solicitado: Negro con tono claro (plata/silver) y nombres grandes
            fig_impacto.update_traces(marker_color='#C0C0C0', marker_line_color='#FFFFFF', marker_line_width=1.5, opacity=0.8)
            fig_impacto.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis={'categoryorder':'total ascending', 'tickfont': {'size': 16, 'color': '#FFFFFF', 'family': 'Inter'}},
                xaxis={'title': 'ACCIONES DE IMPACTO', 'tickfont': {'size': 12}}
            )
            st.plotly_chart(fig_impacto, use_container_width=True)

    with tab2:
        players = sorted(df_match['JUGADOR'].unique())
        sel_p = st.selectbox("👤 JUGADOR", players)
        p_data = df_match[df_match['JUGADOR'] == sel_p].iloc[0]
        
        c1, c2 = st.columns([1, 1])
        with c1:
            stats_p = pd.DataFrame({'Acción': cols_stats, 'Valor': [p_data[c] for c in cols_stats]})
            stats_p = stats_p[stats_p['Valor'] > 0]
            fig_p = px.line_polar(stats_p, r='Valor', theta='Acción', line_close=True, template='plotly_dark')
            fig_p.update_traces(fill='toself', line_color='#FFF', fillcolor='rgba(255,255,255,0.2)')
            st.plotly_chart(fig_p, use_container_width=True)
        with c2:
            st.markdown(f"<h2 style='font-weight:900;'>{sel_p}</h2>", unsafe_allow_html=True)
            p_int_data = df_int[df_int['JUGADOR'] == sel_p]
            if not p_int_data.empty:
                st.markdown(f'<div class="metric-card-uni"><p class="metric-val">{p_int_data.iloc[0]["INTENS."]:.2f}</p><p class="metric-label">Intensidad</p></div>', unsafe_allow_html=True)
            st.table(stats_p)

    with tab3:
        st.markdown("<h2 class='section-title'>MATRIZ DE INTENSIDAD</h2>", unsafe_allow_html=True)
        if not df_int.empty:
            fig_bub = px.scatter(df_int, x='INTENS.', y='EFICIENCIA', size='Acciones', color='INTENS.', text='JUGADOR', template='plotly_dark', height=800, labels={'INTENS.': 'Intensidad (Acc/Min)', 'EFICIENCIA': 'Ratio de Errores'})
            fig_bub.update_traces(textposition='top center', marker=dict(line=dict(width=2, color='white')))
            st.plotly_chart(fig_bub, use_container_width=True)
