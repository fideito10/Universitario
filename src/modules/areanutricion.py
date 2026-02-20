import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import re
from google.oauth2.service_account import Credentials
import gspread
import json

# =============================================================================
# 🔧 CONFIGURACIÓN DE CONEXIÓN Y CREDENCIALES (NO MODIFICAR SEGÚN USUARIO)
# =============================================================================

def get_google_credentials():
    try:
        if hasattr(st, 'secrets') and "google" in st.secrets:
            return dict(st.secrets["google"])
    except Exception: pass
    
    try:
        possible_paths = ["credentials/service-account-key.json", "../credentials/service-account-key.json", "credentials/service_account.json"]
        for cred_path in possible_paths:
            if os.path.exists(cred_path):
                with open(cred_path) as f: return json.load(f)
        return None
    except Exception: return None

def read_google_sheet_as_df(sheet_id, worksheet_name):
    try:
        creds_info = get_google_credentials()
        if not creds_info: return None
        gc = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(worksheet_name)
        # Usar get_all_values() para obtener strings puros y evitar errores de interpretación de comas/puntos
        data = worksheet.get_all_values()
        if not data: return pd.DataFrame()
        # Primera fila como columnas, el resto como datos
        df = pd.DataFrame(data[1:], columns=data[0])
        return df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
    except Exception as e:
        st.error(f"❌ Error leyendo Sheet: {str(e)}")
        return None

def conectar_base_central():
    DATABASE_SHEET_ID = '1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw'
    try:
        creds_info = get_google_credentials()
        gc = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        sh = gc.open_by_key(DATABASE_SHEET_ID)
        ws = sh.get_worksheet(0)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        jugadores = []
        for _, r in df.iterrows():
            nombre = f"{str(r.get('Nombre', '')).strip()} {str(r.get('Apellido', '')).strip()}".strip()
            if not nombre or nombre == "": nombre = str(r.get('Nombre y Apellido', '')).strip()
            jugadores.append({
                'nombre': nombre,
                'dni': str(r.get('DNI', '')).strip(),
                'categoria': str(r.get('Categoria', 'Sin Categoría')).strip(),
                'posicion': str(r.get('Posicion', '')).strip()
            })
        return [j for j in jugadores if j['nombre']]
    except: return []

def guardar_reporte_seguro(row_data):
    try:
        creds_info = get_google_credentials()
        gc = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        sh = gc.open_by_key('1CpAklgxgcVJrIWRWt-yJW4u6EkTcIeQqqp87kllsUqo')
        ws = sh.worksheet("Respuestas de formulario 1")
        values = ws.get_all_values()
        next_row = len(values) + 1
        ws.insert_row(row_data, index=next_row, value_input_option="RAW")
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar en Sheets: {str(e)}")
        return False

# =============================================================================
# 📈 FUNCIONES DE APOYO (LIMPIEZA Y CÁLCULO)
# =============================================================================

def norm(col_name):
    """Normaliza nombres de columnas para búsqueda flexible."""
    return re.sub(r'[^a-z0-9]', '', str(col_name).lower())

def to_num(val):
    """Convierte valores a float manejando comas y errores de forma robusta."""
    if val is None or val == "" or str(val).strip() == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    try:
        # Limpiamos el string y reemplazamos la coma por punto para el float de Python
        s_val = str(val).replace('kg', '').replace('%', '').strip()
        return float(s_val.replace(',', '.'))
    except:
        return 0.0

def f_ar(v):
    """Formatea número para visualización y guardado en Sheets (Estilo AR con coma)."""
    try:
        val = to_num(v)
        # Retornamos string con coma para que Google Sheet lo tome como número en su región
        return f"{val:.1f}".replace('.', ',')
    except:
        return str(v).replace('.', ',')

def format_df_ar(df):
    """Formatea un DataFrame completo para mostrar comas en lugar de puntos en números."""
    df_fmt = df.copy()
    for col in df_fmt.columns:
        # Si la columna es numérica (float o int), la convertimos a string con coma
        if pd.api.types.is_numeric_dtype(df_fmt[col]):
            df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.2f}".replace('.', ',') if pd.notna(x) else "")
        else:
            # Si es string, intentamos detectar si es un número con punto para cambiarlo
            df_fmt[col] = df_fmt[col].apply(lambda x: str(x).replace('.', ',') if isinstance(x, str) and re.match(r'^-?\d+\.\d+$', x) else x)
    return df_fmt

def style_nutricion_df(df):
    """Aplica colores de fondo a las filas según el objetivo nutricional."""
    if df is None or df.empty: return df
    
    col_obj = next((c for c in df.columns if 'objetivo' in c.lower()), None)
    if not col_obj: return df

    def highlight_rows(row):
        val = str(row.get(col_obj, '')).strip()
        # Usamos colores con transparencia (rgba) para que el texto sea legible y se vea premium
        if "Aumento MM" in val:
            return ['background-color: rgba(255, 193, 7, 0.25)'] * len(row)
        elif "Descenso MA" in val:
            return ['background-color: rgba(235, 87, 87, 0.25)'] * len(row)
        elif "Mantenimiento" in val:
            return ['background-color: rgba(39, 174, 96, 0.25)'] * len(row)
        return [''] * len(row)

    return df.style.apply(highlight_rows, axis=1)

def obtener_columna_fecha(df):
    posibles = ['Marca temporal', 'Fecha']
    for col in df.columns:
        if col in posibles or any(p in col.lower() for p in ['fecha', 'date', 'time', 'marca']):
            return col
    return None

# =============================================================================
# 📊 GRÁFICOS PREMIUM
# =============================================================================

def grafico_evolucion_peso(df_hist):
    """Visualización premium de la evolución del peso con formato AR y meses en ES."""
    col_fecha = obtener_columna_fecha(df_hist)
    # Buscar columna de peso de forma muy flexible (contiene 'peso' y 'kg')
    col_peso = next((c for c in df_hist.columns if 'peso' in c.lower() and 'kg' in c.lower()), None)
    
    if col_fecha and col_peso:
        df = df_hist.copy()
        
        # Intentar convertir fecha con manejo de errores robusto
        df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
        
        # Convertir peso usando nuestra función to_num que maneja comas
        df[col_peso] = df[col_peso].apply(to_num)
        
        # Limpiar y ordenar (ASEGURAMOS QUE NO SE PIERDAN DATOS POR DROPN@)
        df = df.dropna(subset=[col_fecha])
        df = df[df[col_peso] > 0]
        df = df.sort_values(col_fecha)
        
        if df.empty: return None
        
        # Mapeo de meses en español para el formato "Mes Año"
        meses_es = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 
                    7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
        
        df['fecha_label'] = df[col_fecha].dt.month.map(meses_es) + " " + df[col_fecha].dt.year.astype(str)
        # Formato con coma para el texto del gráfico
        df['peso_ar'] = df[col_peso].apply(lambda x: f"{float(x):.1f}".replace('.', ',')) + " kg"
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[col_fecha], 
            y=df[col_peso], 
            mode='lines+markers+text',
            line=dict(shape='spline', color='#f2c94c', width=4),
            marker=dict(color='#f2c94c', size=12, line=dict(color='white', width=2)),
            text=df['peso_ar'],
            textposition="top center", 
            customdata=df['fecha_label'],
            hovertemplate="<b>Peso:</b> %{text}<br><b>Fecha:</b> %{customdata}<extra></extra>"
        ))
        
        fig.update_layout(
            title=dict(text="Evolución del Peso (kg)", x=0.5, font=dict(color='white', size=22)),
            plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a',
            xaxis=dict(
                tickmode='array',
                tickvals=df[col_fecha],
                ticktext=df['fecha_label'],
                tickfont=dict(color='white'), 
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(tickfont=dict(color='white'), gridcolor='rgba(255,255,255,0.1)'),
            font=dict(color='white'), height=400, margin=dict(l=40, r=40, t=60, b=40)
        )
        return fig
    return None

def grafico_torta_antropometria(df_hist):
    """Gráfico de torta premium de composición corporal (ÚLTIMO registro)."""
    if df_hist is None or df_hist.empty:
        return None

    date_col = obtener_columna_fecha(df_hist)
    df_copy = df_hist.copy()
    if date_col:
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col]).sort_values(by=date_col)
    
    ultimo = df_copy.iloc[-1] if not df_copy.empty else df_hist.iloc[-1]

    v_muscular = 0.0
    v_osea = 0.0
    v_adiposa = 0.0
    v_peso = 0.0
    v_pct_ma = 0.0

    # Mapeo según especificaciones
    for c in df_hist.columns:
        n = norm(c)
        val = to_num(ultimo.get(c))
        
        if 'peso' in n and 'kg' in n: v_peso = val
        if any(x in n for x in ['kgmm', 'masamuscular', 'cuantoskilosdemasamuscular']):
            if val > 0: v_muscular = val
        if any(x in n for x in ['kgmo', 'masaosea', 'kgdemo', 'mo']):
            if val > 0: v_osea = val
        if any(x in n for x in ['kgma', 'masaadip', 'masaadipos']):
            if val > 0: v_adiposa = val
        if any(x in n for x in ['pctma', 'porcentajema', 'porcentajemasaadiposa']) or ('%' in c and ('ma' in n or 'adip' in n)):
            if val > 0: v_pct_ma = val

    # Si no hay KG de grasa pero hay %, calcular
    if v_adiposa == 0 and v_pct_ma > 0 and v_peso > 0:
        v_adiposa = v_peso * (v_pct_ma / 100.0)

    labels = []
    values = []
    colors_list = []

    # Masa Ósea (#7DA2AB)
    if v_osea > 0:
        labels.append('Masa Ósea')
        values.append(v_osea)
        colors_list.append("#7DA2AB")
    
    # Masa Muscular (#C40404)
    if v_muscular > 0:
        labels.append('Masa Muscular')
        values.append(v_muscular)
        colors_list.append("#C40404")
        
    # Masa Adiposa (#F1E107)
    if v_adiposa > 0:
        label_txt = f"Masa Adiposa ({f_ar(v_pct_ma)}%)" if v_pct_ma > 0 else "Masa Adiposa"
        labels.append(label_txt)
        values.append(v_adiposa)
        colors_list.append("#F1E107")

    # Fallback (#A36309)
    if not labels and v_peso > 0:
        labels = ['Peso Total']
        values = [v_peso]
        colors_list = ["#A36309"]

    if labels:
        text_labels = [f"{l}<br>{f_ar(v)} kg" for l, v in zip(labels, values)]
        fig = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.45,
            marker=dict(colors=colors_list, line=dict(color='#1a1a1a', width=2)),
            text=text_labels,
            textinfo='label+percent', 
            textposition='inside',
            hovertemplate="<b>%{label}</b><br>Peso: %{text}<br>%{percent}<extra></extra>"
        )])

        fig.update_layout(
            title=dict(text="Composición corporal (última antropometría)", x=0.5, font=dict(color='white', size=22)),
            height=380, plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font=dict(color='white'),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=12)),
            margin=dict(l=20, r=20, t=60, b=40)
        )
        # Centro del donut
        fig.add_annotation(
            text=f"<b style='font-size:24px'>{f_ar(v_peso)} kg</b><br><span style='font-size:16px'>Peso</span>",
            showarrow=False, font=dict(color='white'), x=0.5, y=0.5
        )
        return fig
    return None

# =============================================================================
# 📊 EQUIPO & SEGUIMIENTO
# =============================================================================

def crear_grafico_objetivos_equipo(df, categoria_filtro="Todas", mes_filtro="Todos"):
    """Gráfico de bloques sólidos por categoría, con filtros de división y mes."""
    col_obj = next((c for c in df.columns if 'objetivo' in c.lower()), None)
    col_nombre = 'Nombre y Apellido'
    
    if not col_obj or df.empty: return None
    
    df_plot = df.copy()
    
    # 1. Asegurar formato de fecha
    col_fecha = obtener_columna_fecha(df_plot)
    if not col_fecha: return None
    
    df_plot[col_fecha] = pd.to_datetime(df_plot[col_fecha], dayfirst=True, errors='coerce')
    df_plot = df_plot.dropna(subset=[col_fecha])
    
    # 2. Crear columna de Mes para filtrar
    meses_es = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 
                7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
    df_plot['periodo'] = df_plot[col_fecha].dt.month.map(meses_es) + " " + df_plot[col_fecha].dt.year.astype(str)
    
    # 3. Aplicar Filtros
    if categoria_filtro != "Todas":
        df_plot = df_plot[df_plot['Categoría'] == categoria_filtro]
    
    if mes_filtro != "Todos":
        df_plot = df_plot[df_plot['periodo'] == mes_filtro]
        
    if df_plot.empty: 
        st.info(f"No hay registros para {categoria_filtro} en {mes_filtro}")
        return None

    # 4. Última foto de cada jugador DENTRO del filtro seleccionado
    df_plot = df_plot.sort_values(col_fecha).drop_duplicates(subset=[col_nombre], keep='last')
    
    # 5. Agrupar por bloques sólidos
    df_resumen = df_plot.groupby(['Categoría', col_obj]).size().reset_index(name='Cantidad')
    
    # 6. Mapa de colores actualizado
    color_map = {
        "Aumento MM": "#FFC107",
        "Descenso MA": "#EB5757",
        "Mantenimiento": "#27AE60",
        "Sin Definir": "#828282"
    }
    
    fig = px.bar(
        df_resumen, 
        x='Categoría', 
        y='Cantidad',
        color=col_obj,
        text=col_obj,
        title=f"Distribución: {categoria_filtro} | Período: {mes_filtro}",
        labels={col_obj: 'Objetivo', 'Cantidad': 'N° Jugadores', 'Categoría': 'División'},
        color_discrete_map=color_map,
        category_orders={"Categoría": sorted(df_plot['Categoría'].unique())}
    )
    
    fig.update_layout(
        barmode='stack',
        plot_bgcolor='#1a1a1a', 
        paper_bgcolor='#1a1a1a', 
        font=dict(color='white', size=16),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        height=550,
        margin=dict(t=80, b=120),
        yaxis=dict(
            title=dict(text="Cantidad de Jugadores", font=dict(size=18)),
            gridcolor='rgba(255,255,255,0.1)',
            dtick=1
        ),
        xaxis=dict(
            title=None,
            tickfont=dict(size=18),
            gridcolor='rgba(255,255,255,0.1)'
        )
    )
    
    fig.update_traces(
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(size=16, color='white'),
        hovertemplate="<b>%{x}</b><br>Objetivo: %{fullData.name}<br>Cantidad: %{y} jugadores<extra></extra>"
    )

    return fig

# =============================================================================
# 🍏 ÁREA DE NUTRICIÓN - INTERFAZ PRINCIPAL
# =============================================================================

def main_nutricion():
    st.markdown("""
    <div style="background: linear-gradient(90deg, #2E7D32 0%, #4CAF50 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; text-align: center; color: white;">
        <h1 style="color: white; margin: 0; font-size: 2.2rem;">🍏 ÁREA DE NUTRICIÓN</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">Club Universitario de La Plata - Gestión Antropométrica</p>
    </div>
    """, unsafe_allow_html=True)

    HOJA_NUTRICION = "Respuestas de formulario 1"
    jugadores_bc = conectar_base_central()
    df_nutricion = read_google_sheet_as_df('1CpAklgxgcVJrIWRWt-yJW4u6EkTcIeQqqp87kllsUqo', HOJA_NUTRICION)

    tab1, tab2 = st.tabs(["👤 Análisis Individual", "👥 Análisis de Equipo"])

    with tab1:
        st.markdown("### 👤 Análisis Individual por Jugador")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            cats = sorted(list(set([j['categoria'] for j in jugadores_bc]))) if jugadores_bc else []
            cat_sel = st.selectbox("📂 Categoría", options=["Todas"] + cats)
        with col_f2:
            filtrados = [j for j in jugadores_bc if cat_sel == "Todas" or j['categoria'] == cat_sel]
            nombres = sorted([j['nombre'] for j in filtrados])
            jugador_sel = st.selectbox(f"👤 Jugador ({len(nombres)})", options=nombres)

        if not st.session_state.get('show_form', False):
            if st.button("➕ Nuevo Reporte", type="primary"):
                st.session_state['show_form'] = True
                st.rerun()

        if st.session_state.get('show_form', False):
            if st.button("⬅️ Volver al Reporte / Cancelar"):
                st.session_state['show_form'] = False
                st.rerun()

            with st.container():
                with st.form("form_nutricion"):
                    j_data = next((j for j in jugadores_bc if j['nombre'] == jugador_sel), {})
                    st.info(f"DNI: {j_data.get('dni')} | Cat: {j_data.get('categoria')} | Pos: {j_data.get('posicion')}")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        peso = st.number_input("Peso (kg)", step=0.1)
                        talla = st.number_input("Talla (cm)", step=0.1)
                        talla_s = st.number_input("Talla sentado (cm)", step=0.1)
                    with c2:
                        imc = st.number_input("IMC", step=0.1)
                        pct_ma = st.number_input("% Masa Adiposa", step=0.1)
                        z_adi = st.number_input("Z Adiposo", step=0.01)
                        seis_p = st.number_input("6 Pliegues (mm)", step=0.1)
                    with c3:
                        kg_mm = st.number_input("kg MM", step=0.1)
                        pct_mm = st.number_input("% MM", step=0.1)
                        z_mm = st.number_input("Z MM", step=0.01)
                        kg_mo = st.number_input("kg de MO", step=0.1)
                    cl1, cl2 = st.columns(2)
                    with cl1:
                        imo = st.number_input("IMO", step=0.01)
                        obj = st.selectbox("Objetivo", ["Mantenimiento", "Aumento MM", "Descenso MA"])
                    with cl2:
                        obs = st.text_area("Observaciones")
                    if st.form_submit_button("💾 Guardar en Google Sheets"):
                        # Preparamos la fecha
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        
                        # MANDAMOS NÚMEROS PUROS (Sin f_ar)
                        row = [
                            fecha_hoy,                  # 1. Marca temporal
                            jugador_sel,                # 2. Nombre y Apellido
                            str(j_data.get('dni', '')), # 3. DNI
                            str(j_data.get('categoria', '')),
                            str(j_data.get('posicion', '')),
                            float(peso),                # 6. Peso (kg)
                            float(talla),               # 7. Talla (cm)
                            float(talla_s),             # 8. Talla sentado (cm)
                            float(kg_mm),               # 9. Kilos Masa Muscular (Antes kg_mm_base)
                            float(imc),                 # 10. IMC
                            float(pct_ma),              # 11. % Masa Adiposa
                            float(z_adi),               # 12. Z Adiposo
                            float(seis_p),              # 13. 6 Pliegues (mm)
                            float(kg_mm),               # 14. kg MM
                            float(pct_mm),              # 15. % MM
                            float(z_mm),                # 16. Z MM
                            float(kg_mo),               # 17. kg de MO
                            float(imo),                 # 18. IMO
                            obj,                        # 19. Objetivo
                            obs                         # 20. Observaciones
                        ]
                        
                        if guardar_reporte_seguro(row):
                            st.success(f"✅ Reporte guardado: {jugador_sel} con {peso} kg")
                            st.session_state['show_form'] = False
                            st.rerun()

        st.markdown("---")
        # SOLO mostrar el reporte si el formulario NO está abierto
        if not st.session_state.get('show_form', False) and jugador_sel and df_nutricion is not None and not df_nutricion.empty:
            j_data = next((j for j in jugadores_bc if j['nombre'] == jugador_sel), {})
            dni_val = str(j_data.get('dni', '')).strip()
            
            # Detectar columna DNI flexiblemente (puede ser 'Dni' o 'DNI')
            col_dni = next((c for c in df_nutricion.columns if c.lower() == 'dni'), 'Dni')
            
            # Filtrado robusto para capturar TODOS los registros
            df_j = df_nutricion[
                (df_nutricion['Nombre y Apellido'].str.strip() == jugador_sel.strip()) | 
                (df_nutricion[col_dni].astype(str).str.strip() == dni_val)
            ]
            
            if not df_j.empty:
                st.markdown(f"## 📊 {jugador_sel}")
                g1, g2 = st.columns(2)
                with g1: 
                    st.markdown("**Evolución del peso**")
                    fig_p = grafico_evolucion_peso(df_j)
                    if fig_p: st.plotly_chart(fig_p, use_container_width=True)
                    else: st.info("No hay suficientes datos de peso.")
                with g2:
                    st.markdown("**Composición corporal**")
                    fig_t = grafico_torta_antropometria(df_j)
                    if fig_t: st.plotly_chart(fig_t, use_container_width=True)
                    else: st.info("No hay suficientes datos de composición corporal.")
                
                st.markdown("#### 📜 Historial de Mediciones")
                # Mostramos la tabla formateada con comas
                st.dataframe(style_nutricion_df(format_df_ar(df_j)), use_container_width=True)
            else: st.info(f"No hay registros para {jugador_sel}")

    with tab2:
        st.markdown("### 👥 Análisis de Equipo")
        if df_nutricion is not None and not df_nutricion.empty:
            # Preparar datos de tiempo para el filtro de mes
            df_temp = df_nutricion.copy()
            col_fecha = obtener_columna_fecha(df_temp)
            meses_disp = ["Todos"]
            if col_fecha:
                df_temp[col_fecha] = pd.to_datetime(df_temp[col_fecha], dayfirst=True, errors='coerce')
                df_temp = df_temp.dropna(subset=[col_fecha]).sort_values(col_fecha, ascending=False)
                meses_es = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 
                            7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
                df_temp['periodo'] = df_temp[col_fecha].dt.month.map(meses_es) + " " + df_temp[col_fecha].dt.year.astype(str)
                meses_disp += df_temp['periodo'].unique().tolist()

            c1, c2, c3 = st.columns([1, 1.5, 1.5])
            with c1:
                st.metric("Mediciones", len(df_nutricion))
            with c2:
                categorias_unicas = sorted(df_nutricion['Categoría'].unique().tolist()) if 'Categoría' in df_nutricion.columns else []
                cat_equipo = st.selectbox("📂 División", options=["Todas"] + categorias_unicas, key="filt_cat_equipo")
            with c3:
                mes_equipo = st.selectbox("📅 Mes/Año", options=meses_disp, key="filt_mes_equipo")
            
            # Filtrar DataFrame para la tabla según los selectores
            df_tabla = df_nutricion.copy()
            if col_fecha:
                df_tabla[col_fecha] = pd.to_datetime(df_tabla[col_fecha], dayfirst=True, errors='coerce')
                df_tabla['periodo'] = df_tabla[col_fecha].dt.month.map(meses_es) + " " + df_tabla[col_fecha].dt.year.astype(str)
            
            if cat_equipo != "Todas":
                df_tabla = df_tabla[df_tabla['Categoría'] == cat_equipo]
            if mes_equipo != "Todos":
                df_tabla = df_tabla[df_tabla['periodo'] == mes_equipo]

            # Gráfico de objetivos con ambos filtros
            fig_team = crear_grafico_objetivos_equipo(df_nutricion, cat_equipo, mes_equipo)
            if fig_team: st.plotly_chart(fig_team, use_container_width=True)
            
            st.markdown(f"#### 📋 Registros Filtrados ({len(df_tabla)})")
            # Mostramos la tabla filtrada, formateada y COLOREADA
            if 'periodo' in df_tabla.columns: df_tabla = df_tabla.drop(columns=['periodo'])
            st.dataframe(style_nutricion_df(format_df_ar(df_tabla)), use_container_width=True)

if __name__ == "__main__":
    main_nutricion()