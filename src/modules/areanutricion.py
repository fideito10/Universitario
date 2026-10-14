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
from src.utils.credentials import get_credentials_dict, get_gspread_client
from src.utils.cache import cache_si_ok
from src.data import backend
import time

# =============================================================================
# 🔧 CONFIGURACIÓN DE CONEXIÓN Y CREDENCIALES
# =============================================================================

def get_google_credentials():
    """
    Obtiene las credenciales de Google usando el módulo centralizado.
    """
    return get_credentials_dict()

@cache_si_ok(ttl=300)
def read_google_sheet_as_df(sheet_id, worksheet_name):
    # Backend PostgreSQL (DATA_BACKEND=postgres): mismo DataFrame, sin tocar Sheets.
    if backend.use_postgres():
        fuente = backend.fuente_para(sheet_id, worksheet_name)
        if fuente:
            df_pg = backend.df_de_fuente(fuente)
            if df_pg is not backend.FALLBACK:
                return df_pg
    try:
        creds_info = get_google_credentials()
        if not creds_info: return None
        gc = get_gspread_client() or gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
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

@cache_si_ok(ttl=300, ok=lambda r: bool(r))
def conectar_base_central():
    DATABASE_SHEET_ID = '1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw'
    try:
        creds_info = get_google_credentials()
        gc = get_gspread_client() or gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
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
    en_db = False
    if backend.use_postgres():
        if not backend.mirror_writes():
            # Destino principal: la base (visible al instante). Sheets solo si la base falla.
            if backend.registrar_reporte("nutricion", row_data):
                return True
        else:
            en_db = None  # espejo: primero Sheets, luego la DB con mirrored_at
    try:
        creds_info = get_google_credentials()
        gc = get_gspread_client() or gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))
        sh = gc.open_by_key('1CpAklgxgcVJrIWRWt-yJW4u6EkTcIeQqqp87kllsUqo')
        ws = sh.worksheet("Respuestas de formulario 1")
        ws.append_row(row_data, value_input_option="RAW")
        if en_db is None:
            backend.registrar_reporte("nutricion", row_data, mirrored_at=time.time())
        st.cache_data.clear()
        return True
    except Exception as e:
        if en_db is None and backend.registrar_reporte("nutricion", row_data):
            st.warning("⚠️ Reporte guardado en la base; no se pudo copiar a Google Sheets.")
            return True
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

# Encabezados reales de la hoja (ej. "% MA: [Número con decimales]", " kg MM: [...]"):
# se toma solo el texto antes de ":" y se normaliza, así el sufijo del Form no molesta.
_CAMPOS_SHEET = {
    'peso':   ['pesokg'],
    'imc':    ['imc'],
    'pct_ma': ['ma', 'masaadiposa', 'masaadiposa'],
    'pct_mm': ['mm'],
    'kg_mm':  ['kgmm', 'cuantoskilosdemasamuscular', 'kilosmasamuscular', 'masamuscular'],
    'kg_mo':  ['kgdemo', 'kgmo', 'masaosea'],
}

def _base_col(c):
    return norm(str(c).split(':')[0].split('[')[0])

def buscar_col(df, campo):
    """Devuelve la columna del DataFrame que corresponde al campo (por nombre exacto normalizado)."""
    bases = {c: _base_col(c) for c in df.columns}
    for clave in _CAMPOS_SHEET.get(campo, []):
        for c, b in bases.items():
            if b == clave:
                return c
    return None

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
            line=dict(shape='spline', color='#f2c94c', width=3),
            marker=dict(color='#f2c94c', size=9, line=dict(color='white', width=1.5)),
            text=df['peso_ar'],
            textposition="top center", 
            customdata=df['fecha_label'],
            hovertemplate="<b>Peso:</b> %{text}<br><b>Fecha:</b> %{customdata}<extra></extra>"
        ))
        
        fig.update_layout(
            title=dict(text=""),
            plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a',
            xaxis=dict(
                tickmode='array',
                tickvals=df[col_fecha],
                ticktext=df['fecha_label'],
                tickfont=dict(color='white', size=10),
                tickangle=-45 if len(df) > 3 else 0,
                gridcolor='rgba(255,255,255,0.1)',
                fixedrange=True
            ),
            yaxis=dict(tickfont=dict(color='white', size=10), gridcolor='rgba(255,255,255,0.1)', fixedrange=True),
            font=dict(color='white'), height=300, margin=dict(l=10, r=20, t=30, b=10)
        )
        fig.update_traces(textfont=dict(size=10, color='white'), cliponaxis=False)
        fig.update_yaxes(automargin=True)
        fig.update_xaxes(automargin=True)
        return fig
    return None

def grafico_torta_antropometria(df_hist):
    """Gráfico de torta premium de composición corporal (ÚLTIMO registro)."""
    if df_hist is None or df_hist.empty:
        return None

    date_col = obtener_columna_fecha(df_hist)
    df_copy = df_hist.copy()
    if date_col:
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], dayfirst=True, errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col]).sort_values(by=date_col)
    
    ultimo = df_copy.iloc[-1] if not df_copy.empty else df_hist.iloc[-1]

    def _v(campo):
        c = buscar_col(df_hist, campo)
        return to_num(ultimo.get(c)) if c else 0.0

    v_peso = _v('peso')
    v_pct_ma = _v('pct_ma')
    v_osea = _v('kg_mo')

    # Masa muscular: "kg MM"; si está vacío, "Cuantos kilos de Masa Muscular"
    v_muscular = 0.0
    for clave in _CAMPOS_SHEET['kg_mm']:
        c = next((c for c in df_hist.columns if _base_col(c) == clave), None)
        if c and to_num(ultimo.get(c)) > 0:
            v_muscular = to_num(ultimo.get(c))
            break

    # La hoja no tiene kg de grasa: se calcula con peso y % de masa adiposa
    v_adiposa = v_peso * (v_pct_ma / 100.0) if v_peso > 0 and v_pct_ma > 0 else 0.0

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
            textinfo='percent',
            textposition='inside',
            textfont=dict(size=13),
            hovertemplate="<b>%{label}</b><br>Peso: %{text}<br>%{percent}<extra></extra>"
        )])

        fig.update_layout(
            title=dict(text=""),
            height=340, plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font=dict(color='white'),
            legend=dict(orientation="h", yanchor="top", y=-0.02, xanchor="center", x=0.5, font=dict(size=11, color='white')),
            margin=dict(l=10, r=10, t=10, b=70)
        )
        # Centro del donut
        fig.add_annotation(
            text=f"<b>{f_ar(v_peso)} kg</b><br>Peso",
            showarrow=False, font=dict(color='white', size=15), x=0.5, y=0.54
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
        labels={col_obj: 'Objetivo', 'Cantidad': 'N° Jugadores', 'Categoría': 'División'},
        color_discrete_map=color_map,
        category_orders={"Categoría": sorted(df_plot['Categoría'].unique())}
    )
    
    fig.update_layout(
        barmode='stack',
        plot_bgcolor='#1a1a1a', 
        paper_bgcolor='#1a1a1a', 
        font=dict(color='white', size=12),
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5, font=dict(color="white", size=11), title=dict(text="")),
        height=400,
        margin=dict(t=10, b=80, l=10, r=10),
        yaxis=dict(
            title=dict(text="Jugadores", font=dict(size=12)),
            gridcolor='rgba(255,255,255,0.1)',
            dtick=1, fixedrange=True
        ),
        xaxis=dict(
            title=dict(text=""),
            tickfont=dict(size=11),
            gridcolor='rgba(255,255,255,0.1)', fixedrange=True
        )
    )
    
    fig.update_traces(
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(size=11, color='white'),
        hovertemplate="<b>%{x}</b><br>Objetivo: %{fullData.name}<br>Cantidad: %{y} jugadores<extra></extra>"
    )

    return fig

# =============================================================================
# 🍏 ÁREA DE NUTRICIÓN - INTERFAZ PRINCIPAL
# =============================================================================


def _find_col(df, *keys, exclude=()):
    """Busca la primera columna cuyo nombre normalizado contiene alguna de las claves."""
    for c in df.columns:
        n = norm(c)
        if any(k in n for k in keys) and not any(e in n for e in exclude):
            return c
    return None

def _col_pct_ma(df):
    return buscar_col(df, 'pct_ma')

def _fmt_fecha(v):
    d = pd.to_datetime(v, dayfirst=True, errors='coerce')
    return d.strftime('%d/%m/%Y') if pd.notna(d) else str(v)

def _card_html(label, value, sub="", color="#4CAF50"):
    sub_html = f'<div class="nu-sub">{sub}</div>' if sub else ''
    return (f'<div class="nu-card" style="border-top:3px solid {color}">'
            f'<div class="nu-lbl">{label}</div><div class="nu-val">{value}</div>{sub_html}</div>')

def _render_resumen_jugador(df_j):
    """Tarjetas 2x2 con la última medición + objetivo."""
    d = df_j.copy()
    cf = obtener_columna_fecha(d)
    if cf:
        d['_f'] = pd.to_datetime(d[cf], dayfirst=True, errors='coerce')
        d = d.sort_values('_f')
    ult = d.iloc[-1]
    prev = d.iloc[-2] if len(d) > 1 else None
    c_peso = next((c for c in d.columns if 'peso' in c.lower() and 'kg' in c.lower()), None)
    c_ma = _col_pct_ma(d)
    c_mm = buscar_col(d, 'kg_mm')
    if c_mm is None or to_num(ult.get(c_mm)) <= 0:
        c_mm = next((c for c in d.columns if _base_col(c) == 'cuantoskilosdemasamuscular'), c_mm)
    c_imc = buscar_col(d, 'imc')
    c_obj = next((c for c in d.columns if 'objetivo' in c.lower()), None)

    def val(c, suf=""):
        if not c: return "—"
        v = to_num(ult.get(c))
        return f"{f_ar(v)}{suf}" if v > 0 else "—"

    sub_peso = ""
    if c_peso and prev is not None:
        a, b = to_num(ult.get(c_peso)), to_num(prev.get(c_peso))
        if a > 0 and b > 0:
            dif = a - b
            sub_peso = f"{'▲' if dif > 0 else '▼' if dif < 0 else '='} {f_ar(abs(dif))} kg vs. anterior"
    fecha_txt = _fmt_fecha(ult.get(cf)) if cf else ""
    html = '<div class="nu-grid">'
    html += _card_html("⚖️ Peso", val(c_peso, " kg"), sub_peso, "#f2c94c")
    html += _card_html("🔥 % Masa adiposa", val(c_ma, "%"), "", "#F1E107")
    html += _card_html("💪 Masa muscular", val(c_mm, " kg"), "", "#C40404")
    html += _card_html("📏 IMC", val(c_imc), "", "#7DA2AB")
    html += '</div>'
    if c_obj and str(ult.get(c_obj, '')).strip():
        o = str(ult.get(c_obj)).strip()
        col = "#FFC107" if "Aumento MM" in o else "#EB5757" if "Descenso MA" in o else "#27AE60" if "Mantenimiento" in o else "#828282"
        html += f'<div class="nu-obj" style="border-left:5px solid {col}"><span>OBJETIVO ACTUAL</span><b>{o}</b></div>'
    if fecha_txt:
        html += f'<div class="nu-fecha">Última medición: {fecha_txt}</div>'
    st.markdown(html, unsafe_allow_html=True)

def _tabla_esencial(df):
    """Columnas esenciales para ver en celular."""
    cf = obtener_columna_fecha(df)
    cols = []
    for c in [cf,
              next((c for c in df.columns if 'peso' in c.lower() and 'kg' in c.lower()), None),
              _col_pct_ma(df),
              next((c for c in df.columns if 'objetivo' in c.lower()), None),
              next((c for c in df.columns if norm(c) == 'imc'), None)]:
        if c and c not in cols:
            cols.append(c)
    return df[cols].copy() if cols else df

def main_nutricion():
    st.markdown("""
    <style>
    .nutri-header { background: linear-gradient(135deg, #000000 0%, #1f1f1f 100%); padding: 1.2rem 1rem; border-radius: 16px; margin-bottom: 1rem; text-align: center; color: white; border-bottom: 4px solid #4CAF50; }
    .nutri-header h1 { color: white; margin: 0; font-size: 1.9rem; letter-spacing: 1px; text-transform: uppercase; }
    .nutri-header p { margin: 0.4rem 0 0 0; opacity: 0.8; font-size: 0.95rem; }
    .nu-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 0.4rem 0 0.6rem 0; }
    .nu-card { background: linear-gradient(135deg, #111 0%, #2a2a2a 100%); border-radius: 14px; padding: 12px 10px; color: #fff; text-align: center; min-width: 0; }
    .nu-lbl { font-size: 0.7rem; text-transform: uppercase; letter-spacing: .5px; opacity: .8; }
    .nu-val { font-size: 1.5rem; font-weight: 800; margin-top: 4px; line-height: 1.15; color: #fff; }
    .nu-sub { font-size: 0.68rem; opacity: .7; margin-top: 3px; }
    .nu-obj { background: #f4f6f4; border-radius: 12px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; gap: 8px; color: #111; }
    .nu-obj span { font-size: 0.7rem; letter-spacing: .5px; opacity: .65; }
    .nu-fecha { font-size: 0.75rem; color: #777; text-align: right; margin-top: 4px; }
    .nu-sec { font-size: 0.95rem; font-weight: 800; text-transform: uppercase; letter-spacing: .5px; margin: 1rem 0 .3rem 0; padding-left: 8px; border-left: 4px solid #4CAF50; }
    @media (max-width: 768px) {
        .nutri-header { padding: 0.9rem 0.6rem; margin-bottom: 0.8rem; }
        .nutri-header h1 { font-size: 1.3rem; }
        .nutri-header p { font-size: 0.8rem; }
        .nu-val { font-size: 1.35rem; }
        div[data-baseweb="select"] > div { min-height: 48px; }
        .stButton > button, .stFormSubmitButton > button { min-height: 48px; width: 100%; }
    }
    </style>
    <div class="nutri-header">
        <h1>🍏 Área de Nutrición</h1>
        <p>Club Universitario de La Plata · Gestión Antropométrica</p>
    </div>
    """, unsafe_allow_html=True)

    user = st.session_state.get('user') or {}
    es_jugador = str(user.get('rol', '')).strip().lower() == "jugador"
    mi_dni = re.sub(r'\D', '', str(user.get('dni', '')))

    HOJA_NUTRICION = "Respuestas de formulario 1"
    jugadores_bc = conectar_base_central()
    df_nutricion = read_google_sheet_as_df('1CpAklgxgcVJrIWRWt-yJW4u6EkTcIeQqqp87kllsUqo', HOJA_NUTRICION)

    tab1, tab2 = st.tabs(["👤 Individual", "👥 Equipo"])

    with tab1:
        # Si el usuario es jugador, preseleccionar su propio nombre (solo valor por defecto)
        idx_default = 0
        if es_jugador and mi_dni and jugadores_bc:
            propios = [j for j in jugadores_bc if re.sub(r'\D', '', j['dni']) == mi_dni]
            if propios:
                nombres_all = sorted(j['nombre'] for j in jugadores_bc)
                idx_default = nombres_all.index(propios[0]['nombre'])
        with st.expander("🔎 Elegir jugador", expanded=not es_jugador):
            cats = sorted(list(set([j['categoria'] for j in jugadores_bc]))) if jugadores_bc else []
            cat_sel = st.selectbox("📂 Categoría", options=["Todas"] + cats)
            filtrados = [j for j in jugadores_bc if cat_sel == "Todas" or j['categoria'] == cat_sel]
            nombres = sorted([j['nombre'] for j in filtrados])
            jugador_sel = st.selectbox(f"👤 Jugador ({len(nombres)})", options=nombres,
                                       index=idx_default if (cat_sel == "Todas" and idx_default < len(nombres)) else 0)

        # Carga de reportes: solo staff (presentación; no altera permisos)
        if not es_jugador:
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


        # SOLO mostrar el reporte si el formulario NO está abierto
        if es_jugador or not st.session_state.get('show_form', False):
            if not jugador_sel or df_nutricion is None or df_nutricion.empty:
                st.info("🍏 Todavía no hay mediciones cargadas. Cuando el staff de nutrición registre una, la vas a ver acá.")
            else:
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
                    st.markdown(f'<div class="nu-sec">📊 {jugador_sel}</div>', unsafe_allow_html=True)
                    _render_resumen_jugador(df_j)

                    t_peso, t_comp, t_hist = st.tabs(["⚖️ Peso", "🧬 Composición", "📜 Historial"])
                    with t_peso:
                        fig_p = grafico_evolucion_peso(df_j)
                        if fig_p: st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})
                        else: st.info("No hay suficientes datos de peso.")
                    with t_comp:
                        st.caption("Última antropometría")
                        fig_t = grafico_torta_antropometria(df_j)
                        if fig_t: st.plotly_chart(fig_t, use_container_width=True, config={"displayModeBar": False})
                        else: st.info("No hay suficientes datos de composición corporal.")
                    with t_hist:
                        df_fmt = format_df_ar(df_j)
                        st.dataframe(style_nutricion_df(_tabla_esencial(df_fmt)), use_container_width=True, hide_index=True)
                        with st.expander("Ver todas las columnas"):
                            st.dataframe(style_nutricion_df(df_fmt), use_container_width=True)
                else:
                    st.info(f"🍏 Todavía no hay mediciones para {jugador_sel}.")

    with tab2:
        if df_nutricion is not None and not df_nutricion.empty:
            # Preparar datos de tiempo para el filtro de mes
            df_temp = df_nutricion.copy()
            col_fecha = obtener_columna_fecha(df_temp)
            meses_disp = ["Todos"]
            meses_es = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio',
                        7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
            if col_fecha:
                df_temp[col_fecha] = pd.to_datetime(df_temp[col_fecha], dayfirst=True, errors='coerce')
                df_temp = df_temp.dropna(subset=[col_fecha]).sort_values(col_fecha, ascending=False)
                df_temp['periodo'] = df_temp[col_fecha].dt.month.map(meses_es) + " " + df_temp[col_fecha].dt.year.astype(str)
                meses_disp += df_temp['periodo'].unique().tolist()

            with st.expander("🔎 Filtros", expanded=False):
                categorias_unicas = sorted(df_nutricion['Categoría'].unique().tolist()) if 'Categoría' in df_nutricion.columns else []
                cat_equipo = st.selectbox("📂 División", options=["Todas"] + categorias_unicas, key="filt_cat_equipo")
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

            st.markdown('<div class="nu-grid">' + _card_html("📋 Mediciones", len(df_nutricion), "", "#4CAF50")
                        + _card_html("🔎 En el filtro", len(df_tabla), f"{cat_equipo} · {mes_equipo}", "#f2c94c") + '</div>',
                        unsafe_allow_html=True)

            # Gráfico de objetivos con ambos filtros
            st.markdown('<div class="nu-sec">🎯 Objetivos por división</div>', unsafe_allow_html=True)
            fig_team = crear_grafico_objetivos_equipo(df_nutricion, cat_equipo, mes_equipo)
            if fig_team: st.plotly_chart(fig_team, use_container_width=True, config={"displayModeBar": False})

            with st.expander(f"📋 Registros filtrados ({len(df_tabla)})", expanded=False):
                if 'periodo' in df_tabla.columns: df_tabla = df_tabla.drop(columns=['periodo'])
                cols_team = [c for c in ['Nombre y Apellido', 'Categoría'] if c in df_tabla.columns]
                cols_team += [c for c in _tabla_esencial(df_tabla).columns if c not in cols_team]
                st.dataframe(style_nutricion_df(format_df_ar(df_tabla[cols_team])), use_container_width=True, hide_index=True)
        else:
            st.info("🍏 Todavía no hay mediciones cargadas.")

if __name__ == "__main__":
    main_nutricion()