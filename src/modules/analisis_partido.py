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
        ws_acum = ss.worksheet("Acciones Acumuladas")
        data_acum = ws_acum.get_all_values()
        df_acum = pd.DataFrame(data_acum[1:], columns=[str(h).strip() for h in data_acum[0]])
        
        ws_int = ss.worksheet("Intensidad Indv.")
        data_int = ws_int.get_all_values()
        header_idx = 0
        for i, row in enumerate(data_int):
            if "Nombre" in row: header_idx = i; break
        df_int = pd.DataFrame(data_int[header_idx+1:], columns=[str(h).strip() for h in data_int[header_idx]])
        
        for col in df_acum.columns:
            if 'RUCK' in col.upper(): df_acum = df_acum.rename(columns={col: 'RUCK'})
        
        rename_map = {'Nombre': 'JUGADOR', 'NF /INTENS,': 'EFICIENCIA', 'Intensidad': 'INTENS.'}
        df_acum = df_acum.rename(columns=rename_map)
        df_int = df_int.rename(columns=rename_map)
        
        match_mapping = {
            '14/3/2026': 'vs. Hurling (F1)', '21/3/2026': 'vs. San Andres (F2)',
            '28/3/2026': 'vs. Pucará (F3)', '11/4/2026': 'vs. Pueyrredón (F4)',
            '18/4/2026': 'vs. San Fernando (F5)', '25/4/2026': 'vs. Dep. Francesa (F6)'
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
    # 1. Inyectar Estilos (Separado del HTML para evitar errores de renderizado)
    st.markdown("""
        <style>
        /* Forzar fondo oscuro en toda la app cuando este modulo este activo */
        [data-testid="stAppViewContainer"] {
            background-color: #000000 !important;
        }
        .stApp { background-color: #000000; color: #FFFFFF; }
        
        .main-header-uni { 
            background: #000000; 
            padding: 2rem; 
            border-radius: 15px; 
            border: 2px solid #FFFFFF; 
            margin-bottom: 2rem; 
            text-align: center; 
        }
        
        .metric-card-uni { 
            background: #111111; 
            border: 1px solid #333; 
            border-radius: 15px; 
            padding: 1.5rem; 
            text-align: center; 
            margin-bottom: 1rem;
        }
        .metric-val { font-size: 3.5rem; font-weight: 900; color: #FFFFFF; margin: 0; line-height: 1; }
        .metric-label { font-size: 1rem; font-weight: 700; color: #888; text-transform: uppercase; margin-top: 0.5rem; }
        
        .top-player-card { 
            background: #0a0a0a; 
            border-radius: 12px; 
            padding: 15px; 
            margin-bottom: 10px; 
            border-left: 5px solid #FFF; 
            border: 1px solid #222;
        }
        .top-player-name { font-size: 1.1rem; font-weight: 900; color: #FFFFFF; text-transform: uppercase; }
        .top-player-stats { font-size: 0.9rem; font-weight: 700; color: #666; }
        
        .section-title { 
            font-size: 2rem; 
            font-weight: 900; 
            color: #FFF;
            border-left: 8px solid #FFF; 
            padding-left: 15px; 
            margin: 2rem 0; 
            text-transform: uppercase; 
        }
        
        .analyst-box { 
            background-color: #050505; 
            border: 1px solid #333; 
            border-radius: 15px; 
            padding: 25px; 
            margin: 30px 0; 
            border-left: 10px solid #FFFFFF; 
        }
        </style>
    """, unsafe_allow_html=True)

    logo_b64 = get_base64_image("escudo uni.jpg")
    
    # 2. Header estable
    with st.container():
        st.markdown(f"""
            <div class="main-header-uni">
                <img src="data:image/jpeg;base64,{logo_b64}" style="width: 80px; margin-bottom:10px;">
                <h1 style='margin: 0; color: white; font-weight: 900;'>PANEL TÁCTICO CULP</h1>
                <p style='color: #888; margin:0;'>ANÁLISIS PROFESIONAL DE RENDIMIENTO</p>
            </div>
        """, unsafe_allow_html=True)

    df_acum, df_int, match_mapping = fetch_rugby_data()
    if df_acum is None: return

    partidos = sorted(df_acum['Partido'].unique())
    selected_match = st.selectbox("🏟️ SELECCIONAR PARTIDO", partidos, index=len(partidos)-1)
    df_match = df_acum[df_acum['Partido'] == selected_match]

    tab1, tab2, tab3 = st.tabs(["📊 RENDIMIENTO", "👤 JUGADORES", "⚡ INTENSIDAD"])

    cols_stats = [c for c in df_match.columns if c not in ['JUGADOR', 'Fecha', 'Partido', 'MINUTOS', 'CHK FECHA', 'CHK NOMBRE', '5', 'TOTAL']]

    with tab1:
        st.markdown(f"<h2 class='section-title'>BALANCE: {selected_match}</h2>", unsafe_allow_html=True)
        
        # Totales
        total_team = df_match[cols_stats].sum()
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="metric-card-uni"><p class="metric-val">{int(total_team.get("TACKLE", 0))}</p><p class="metric-label">Tackles</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card-uni"><p class="metric-val">{int(total_team.get("QUIEBRE", 0))}</p><p class="metric-label">Quiebres</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card-uni"><p class="metric-val">{int(total_team.get("PENAL", 0))}</p><p class="metric-label">Penales</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card-uni"><p class="metric-val">{int(total_team.get("NO FORZADO", 0))}</p><p class="metric-label">E. No Forzados</p></div>', unsafe_allow_html=True)

        st.markdown("<h2 class='section-title'>🏆 LÍDERES</h2>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        
        def render_top3(column, title, emoji):
            if column not in df_match.columns: return
            top = df_match.sort_values(by=column, ascending=False).head(3)
            st.markdown(f"**{emoji} {title}**")
            for idx, row in top.iterrows():
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
            <h4 style='color: #FFF; font-weight:900;'>📝 ANÁLISIS DEL STAFF</h4>
            <p style='color: #CCC;'>
                Se observa un sólido desempeño en la base. El objetivo es reducir los {nf_val} errores no forzados para dominar la posesión.
            </p>
        </div>""", unsafe_allow_html=True)

        st.markdown("<h2 class='section-title'>📊 GRÁFICOS</h2>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            radar_labels = ['Tackles', 'Quiebres', 'Pescas', 'Penales (inv)', 'E.NF (inv)']
            radar_vals = [total_team.get('TACKLE', 0)/5, total_team.get('QUIEBRE', 0)*2, total_team.get('PESCA', 0)*2, max(0, 20-total_team.get('PENAL', 0)), max(0, 20-total_team.get('NO FORZADO', 0))]
            fig_r = go.Figure(data=go.Scatterpolar(r=radar_vals, theta=radar_labels, fill='toself', line_color='#FFF', fillcolor='rgba(255,255,255,0.2)'))
            fig_r.update_layout(polar=dict(radialaxis=dict(visible=False)), showlegend=False, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_r, use_container_width=True)
        with g2:
            df_match['IMPACTO'] = df_match['TACKLE'] + df_match['QUIEBRE'] + df_match['PESCA']
            top10 = df_match.sort_values(by='IMPACTO', ascending=False).head(10)
            fig_i = px.bar(top10, x='IMPACTO', y='JUGADOR', orientation='h', template='plotly_dark')
            fig_i.update_traces(marker_color='#C0C0C0')
            fig_i.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis={'tickfont': {'size': 14}})
            st.plotly_chart(fig_i, use_container_width=True)

    with tab2:
        players = sorted(df_match['JUGADOR'].unique())
        sel_p = st.selectbox("👤 JUGADOR", players)
        p_data = df_match[df_match['JUGADOR'] == sel_p].iloc[0]
        st.markdown(f"## {sel_p}")
        st.table(pd.DataFrame({'Acción': cols_stats, 'Valor': [p_data[c] for c in cols_stats]}).query('Valor > 0'))

    with tab3:
        if not df_int.empty:
            fig_bub = px.scatter(df_int, x='INTENS.', y='EFICIENCIA', size='Acciones', color='INTENS.', text='JUGADOR', template='plotly_dark', height=600)
            st.plotly_chart(fig_bub, use_container_width=True)
