"""
Interfaz de Formularios Médicos con Streamlit
Sistema completo de captura y visualización de datos médicos
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import json
import sys
import os
def get_google_credentials():
    """
    Obtiene las credenciales de Google de forma segura desde st.secrets o archivo local
    """
    try:
        # Primero intentar obtener desde st.secrets (para Streamlit Cloud)
        if hasattr(st, 'secrets') and "google" in st.secrets:
            return dict(st.secrets["google"])
    except Exception:
        pass
    
    # Si estamos local o no hay secrets, leer archivo
    try:
        possible_paths = [
            "credentials/service-account-key.json",
            "../credentials/service-account-key.json",
            "credentials/service_account.json",
            "../credentials/service_account.json", 
            "credentials/car-digital-441319-1a4e4b5c11c2.json",
            "../credentials/car-digital-441319-1a4e4b5c11c2.json"
        ]
        
        for cred_path in possible_paths:
            if os.path.exists(cred_path):
                with open(cred_path) as f:
                    return json.load(f)
        
        raise FileNotFoundError("No se encontró archivo de credenciales")
        
    except Exception as e:
        st.error(f"❌ Error cargando credenciales: {e}")
        return None

# Importaciones opcionales
try:
    from sheets.formularios_google_sheets import FormulariosGoogleSheets
except ImportError:
    FormulariosGoogleSheets = None

try:
    from .auth_manager import AuthManager
except ImportError:
    try:
        from auth_manager import AuthManager
    except ImportError:
        AuthManager = None

import gspread
from google.oauth2.service_account import Credentials

# Variables globales
creds_info = None
creds = None




def read_google_sheet_with_headers(sheet_id=None, worksheet_name=None, credentials_path=None):
    """
    Lee un Google Sheet usando la primera fila como nombres de columnas
    """
    global creds_info, creds
    
    # Configuración por defecto
    if sheet_id is None:
        sheet_id = '1ham2WSMQa3eEv0V0TtHcAa55R3WLGoBje6pSOoNxcBQ'
    
    # Cargar credenciales solo cuando se necesiten
    if creds_info is None:
        creds_info = get_google_credentials()
        
    if creds_info is None:
        return {
            'success': False,
            'data': None,
            'columns': None,
            'message': 'No se pudieron cargar las credenciales de Google'
        }
    
    try:
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Crear credenciales solo cuando se necesiten
        if creds is None:
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        
        gc = gspread.authorize(creds)
        
        # Abrir el Google Sheet
        sh = gc.open_by_key(sheet_id)
        
        # Seleccionar la hoja de trabajo - MEJORADO
        if worksheet_name:
            worksheet = sh.worksheet(worksheet_name)
        else:
            worksheets = sh.worksheets()
            worksheet = None
            
            # Usar la primera hoja por defecto (gid=0)
            worksheet = sh.get_worksheet(0)
        
        # Leer todos los datos
        all_data = worksheet.get_all_values()
        
        if not all_data:
            return {
                'success': False,
                'data': None,
                'columns': None,
                'message': 'La hoja está vacía'
            }
        
        # Primera fila como columnas
        columns = all_data[0]
        data_rows = all_data[1:]
        
        # Crear lista de diccionarios
        structured_data = []
        for row in data_rows:
            row_data = {}
            for i, column in enumerate(columns):
                value = row[i] if i < len(row) else ''
                row_data[column] = value
            structured_data.append(row_data)
        
        return {
            'success': True,
            'data': structured_data,
            'columns': columns,
            'raw_data': data_rows,
            'total_rows': len(data_rows),
            'sheet_title': sh.title,
            'worksheet_title': worksheet.title,
            'message': f'Datos leídos exitosamente: {len(data_rows)} filas, {len(columns)} columnas'
        }
        
    except gspread.exceptions.SpreadsheetNotFound:
        return {
            'success': False,
            'data': None,
            'columns': None,
            'message': 'Google Sheet no encontrado. Verifica el ID y permisos.'
        }
        
    except gspread.exceptions.APIError as e:
        return {
            'success': False,
            'data': None,
            'columns': None,
            'message': f'Error de API: {e}. Verifica que hayas compartido el sheet con la cuenta de servicio.'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'columns': None,
            'message': f'Error inesperado: {e}'
        }

def create_dataframe_from_sheet(sheet_id=None, worksheet_name=None):
    """
    Crea un DataFrame de pandas desde el Google Sheet
    """
    result = read_google_sheet_with_headers(sheet_id, worksheet_name)
    
    if result['success']:
        df = pd.DataFrame(result['data'])
        return df
    else:
        return None

def mostrar_resumen_datos(df):
    """
    Muestra resumen estadístico de los datos con tarjetas métricas
    """
    # Calcular métricas
    total_lesionados = len(df)
    
    if 'Severidad de la lesión' in df.columns:
        en_recuperacion = len(df[df['Severidad de la lesión'].str.contains('Leve|Moderada', case=False, na=False)])
        recuperados = len(df[df['Severidad de la lesión'].str.contains('Leve \(1-7 días\)', case=False, na=False)])
        casos_graves = len(df[df['Severidad de la lesión'].str.contains('Grave|Muy grave', case=False, na=False)])
    else:
        en_recuperacion = 0
        recuperados = 0
        casos_graves = 0
    
    # Tarjetas métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Lesiones Totales", total_lesionados)
    with col2:
        st.metric("🔄 En Recuperación", en_recuperacion)
    with col3:
        st.metric("✅ Recuperados", recuperados)
    with col4:
        st.metric("⚠️ Casos Graves", casos_graves)

def mostrar_filtros_jugador_categoria(df):
    """
    Muestra filtros por categoría y jugador con información detallada
    """
    st.markdown("### 🔍 Filtros por Categoría y Jugador")
    
    # Nombres de columnas
    col_categoria = 'Categoría'
    col_jugador = 'Nombre del Paciente'
    
    # Filtros en columnas
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        # FILTRO IZQUIERDO - CATEGORÍAS
        if col_categoria in df.columns:
            categorias_disponibles = ['Todas'] + sorted(df[col_categoria].dropna().unique().tolist())
            categoria_seleccionada = st.selectbox(
                "🏈 Seleccionar División",
                categorias_disponibles,
                key="area_medica_filtro_categoria"
            )
        else:
            categoria_seleccionada = 'Todas'
    
    with col_filtro2:
        # FILTRO DERECHO - JUGADORES (FILTRADOS POR CATEGORÍA)
        if col_jugador in df.columns:
            # AQUÍ ESTÁ LA MAGIA: Si hay categoría seleccionada, filtra los jugadores
            if categoria_seleccionada != 'Todas':
                jugadores_filtrados = df[df[col_categoria] == categoria_seleccionada][col_jugador].dropna().unique()
            else:
                jugadores_filtrados = df[col_jugador].dropna().unique()
            
            jugadores_disponibles = ['Todos'] + sorted(jugadores_filtrados.tolist())
            jugador_seleccionado = st.selectbox(
                "👤 Seleccionar Jugador",
                jugadores_disponibles,
                key="area_medica_filtro_jugador"
            )
        else:
            jugador_seleccionado = 'Todos'
    
    # Aplicar filtros al DataFrame
    df_filtrado = df.copy()
    
    # Aplicar filtro de categoría
    if categoria_seleccionada != 'Todas' and col_categoria in df.columns:
        df_filtrado = df_filtrado[df_filtrado[col_categoria] == categoria_seleccionada]
    
    # Aplicar filtro de jugador específico
    if jugador_seleccionado != 'Todos' and col_jugador in df.columns:
        df_filtrado = df_filtrado[df_filtrado[col_jugador] == jugador_seleccionado]
    
    # Mostrar información de filtros aplicados
    info_filtros = []
    if categoria_seleccionada != 'Todas':
        info_filtros.append(f"**División:** {categoria_seleccionada}")
    if jugador_seleccionado != 'Todos':
        info_filtros.append(f"**Jugador:** {jugador_seleccionado}")
    
    if info_filtros:
        st.info(f"🔍 **Filtros activos:** {' | '.join(info_filtros)}")
    
    # Mostrar resultados filtrados
    if not df_filtrado.empty:
        st.success(f"✅ **{len(df_filtrado)} registro(s) encontrado(s)**")
        
        # Si es un jugador específico, mostrar información detallada
        if jugador_seleccionado != 'Todos':
            st.markdown(f"#### 👤 Historial Médico de {jugador_seleccionado}")
            
            # Mostrar resumen del jugador
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📋 Total Lesiones", len(df_filtrado))
            with col2:
                if 'Severidad de la lesión' in df_filtrado.columns:
                    graves = len(df_filtrado[df_filtrado['Severidad de la lesión'].str.contains('Grave', case=False, na=False)])
                    st.metric("⚠️ Lesiones Graves", graves)
                else:
                    st.metric("⚠️ Lesiones Graves", "N/A")
            with col3:
                if 'Fecha' in df_filtrado.columns:
                    try:
                        fechas = pd.to_datetime(df_filtrado['Fecha'], errors='coerce').dropna()
                        if not fechas.empty:
                            ultima_lesion = fechas.max().strftime('%d/%m/%Y')
                            st.metric("📅 Última Lesión", ultima_lesion)
                        else:
                            st.metric("📅 Última Lesión", "N/A")
                    except:
                        st.metric("📅 Última Lesión", "N/A")
        
        # Mostrar tabla de datos
        st.dataframe(df_filtrado, use_container_width=True, height=400)
        
        # Botón para descargar datos filtrados
        if len(df_filtrado) > 0:
            csv = df_filtrado.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos filtrados",
                data=csv,
                file_name=f"lesiones_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("⚠️ No se encontraron registros con los filtros seleccionados")
    
    # Devolver el DataFrame filtrado para uso en otras funciones
    return df_filtrado

def test_google_connection():
    """
    Prueba la conexión con Google Sheets y muestra información de diagnóstico
    """
    st.sidebar.markdown("### 🧪 Test de Conexión")
    
    if st.sidebar.button("🔗 Probar Conexión"):
        with st.sidebar.spinner("Probando conexión..."):
            # Test básico de credenciales
            creds = get_google_credentials()
            if creds is None:
                st.sidebar.error("❌ No se encontraron credenciales")
                return
            
            st.sidebar.success("✅ Credenciales cargadas")
            
            # Test de conexión al sheet
            result = read_google_sheet_with_headers()
            
            if result['success']:
                st.sidebar.success(f"✅ Conexión exitosa")
                st.sidebar.info(f"📊 {result['total_rows']} filas, {len(result['columns'])} columnas")
                
                with st.sidebar.expander("Ver detalles"):
                    st.write("**Información del Sheet:**")
                    st.write(f"- Título: {result.get('sheet_title', 'N/A')}")
                    st.write(f"- Hoja: {result.get('worksheet_title', 'N/A')}")
                    st.write(f"- Mensaje: {result['message']}")
                    
                    st.write("**Columnas encontradas:**")
                    for i, col in enumerate(result['columns']):
                        st.write(f"{i+1}. `{col}`")
            else:
                st.sidebar.error(f"❌ Error: {result['message']}")

def mostrar_graficos_interactivos(df):
    """
    Muestra gráficos interactivos con filtros
    """
    st.markdown("### 📊 Análisis de Lesiones")
    
    # Nombres de columnas
    col_categoria = 'Categoría'
    col_severidad = 'Severidad de la lesión'
    
    # Limpiar datos
    if col_severidad in df.columns:
        df[col_severidad] = df[col_severidad].str.strip()
    
    # Gráficos
    if col_categoria in df.columns and not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Lesiones por División")
            categorias_counts = df[col_categoria].value_counts()
            
            fig = px.bar(
                x=categorias_counts.index,
                y=categorias_counts.values,
                color_discrete_sequence=['#1e40af', '#2563eb', '#3b82f6']
            )
            
            fig.update_layout(
                showlegend=False,
                xaxis_title="División",
                yaxis_title="Cantidad",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if col_severidad in df.columns:
                st.markdown("#### 🎯 Distribución por Severidad")
                severidad_counts = df[col_severidad].value_counts()
                
                fig_pie = px.pie(
                    values=severidad_counts.values,
                    names=severidad_counts.index,
                    color_discrete_sequence=['#22c55e', '#eab308', '#ef4444', '#dc2626']
                )
                
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)



def append_google_sheet_row(sheet_id, worksheet_name, row_data, credentials_dict):
    """Agrega una fila a una hoja de Google Sheets. Robustez mejorada para selección de hoja."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    
    ws = None
    if worksheet_name:
        try:
            ws = sh.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            st.warning(f"⚠️ Hoja '{worksheet_name}' no encontrada. Usando la primera hoja.")
            ws = sh.get_worksheet(0)
    else:
        ws = sh.get_worksheet(0)
        
    ws.append_row(row_data, value_input_option="USER_ENTERED")
    return True
# Agregar después de la función mostrar_graficos_interactivos:

def mostrar_timeline_lesiones(df):
    """
    Muestra timeline de lesiones por fecha
    """
    if 'Fecha' in df.columns and not df.empty:
        st.markdown("#### 📅 Timeline de Lesiones")
        
        # Convertir fechas
        df_timeline = df.copy()
        df_timeline['Fecha'] = pd.to_datetime(df_timeline['Fecha'], errors='coerce')
        df_timeline = df_timeline.dropna(subset=['Fecha'])
        
        if not df_timeline.empty:
            # Agrupar por fecha
            lesiones_por_fecha = df_timeline.groupby(df_timeline['Fecha'].dt.date).size().reset_index()
            lesiones_por_fecha.columns = ['Fecha', 'Cantidad']
            
            fig = px.line(
                lesiones_por_fecha, 
                x='Fecha', 
                y='Cantidad',
                title="Evolución Temporal de Lesiones",
                markers=True
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

def mostrar_estadisticas_avanzadas(df):
    """
    Estadísticas avanzadas y alertas
    """
    if not df.empty:
        st.markdown("#### 🚨 Alertas y Estadísticas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Jugadores con más lesiones
            if 'Nombre del Paciente' in df.columns:
                jugadores_frecuentes = df['Nombre del Paciente'].value_counts().head(5)
                
                if len(jugadores_frecuentes) > 0:
                    st.warning("⚠️ **Jugadores con más lesiones:**")
                    for jugador, cantidad in jugadores_frecuentes.items():
                        if cantidad > 2:  # Alerta si tiene más de 2 lesiones
                            st.write(f"🔴 {jugador}: {cantidad} lesiones")
                        else:
                            st.write(f"🟡 {jugador}: {cantidad} lesiones")
        
        with col2:
            # Divisiones más afectadas
            if 'Categoría' in df.columns:
                divisiones_afectadas = df['Categoría'].value_counts()
                
                st.info("📊 **Divisiones más afectadas:**")
                for division, cantidad in divisiones_afectadas.items():
                    porcentaje = (cantidad / len(df)) * 100
                    st.write(f"🏈 {division}: {cantidad} ({porcentaje:.1f}%)")


def main_streamlit():
    """
    INTERFAZ PRINCIPAL - ÚNICA FUNCIÓN MAIN
    """
    # Header
    st.markdown("""
    <div style="background: linear-gradient(135deg, #000000 0%, #2C2C2C 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">🏥 Área Médica - Universitario</h1>
        <p style="color: rgba(255,255,255,0.9); text-align: center; margin: 0.5rem 0 0 0;">Sistema Integral de Gestión Médica</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    with st.spinner("🔄 Cargando datos desde Google Sheets..."):
        try:
            df = create_dataframe_from_sheet()
            
            if df is not None and not df.empty:
                # Nombres de columnas
                col_categoria = 'Categoría'
                col_severidad = 'Severidad de la lesión'
                
                # FILTROS EN FILA HORIZONTAL
                st.markdown("### 🔍 Filtros")
                col_filtro1, col_filtro2 = st.columns(2)
                
                with col_filtro1:
                    # Filtro de Categoría
                    if col_categoria in df.columns:
                        categorias_disponibles = ['Todas'] + sorted(df[col_categoria].dropna().unique().tolist())
                        categoria_seleccionada = st.selectbox(
                            "🏈 Seleccionar División",
                            categorias_disponibles,
                            key="area_medica_filtro_categoria"
                        )
                    else:
                        categoria_seleccionada = 'Todas'
                
                with col_filtro2:
                    # Filtro de Gravedad
                    if col_severidad in df.columns:
                        gravedades_disponibles = ['Todas'] + sorted(df[col_severidad].dropna().unique().tolist())
                        gravedad_seleccionada = st.selectbox(
                            "⚠️ Seleccionar Gravedad",
                            gravedades_disponibles,
                            key="area_medica_filtro_gravedad"
                        )
                    else:
                        gravedad_seleccionada = 'Todas'
                
                # Aplicar filtros al DataFrame
                df_filtrado = df.copy()
                
                if categoria_seleccionada != 'Todas' and col_categoria in df.columns:
                    df_filtrado = df_filtrado[df_filtrado[col_categoria] == categoria_seleccionada]
                
                if gravedad_seleccionada != 'Todas' and col_severidad in df.columns:
                    df_filtrado = df_filtrado[df_filtrado[col_severidad] == gravedad_seleccionada]
                
                # Mostrar información de filtros aplicados
                info_filtros = []
                if categoria_seleccionada != 'Todas':
                    info_filtros.append(f"**División:** {categoria_seleccionada}")
                if gravedad_seleccionada != 'Todas':
                    info_filtros.append(f"**Gravedad:** {gravedad_seleccionada}")
                
                if info_filtros:
                    st.info(f"🔍 **Filtros activos:** {' | '.join(info_filtros)}")
                
                st.markdown("---")
                
                # GRÁFICOS EN FILA HORIZONTAL
                st.markdown("### 📊 Análisis de Lesiones")
                col_grafico1, col_grafico2 = st.columns(2)
                
                with col_grafico1:
                    # Gráfico por Categoría
                    st.markdown("#### 📊 Lesiones por División")
                    if col_categoria in df_filtrado.columns and not df_filtrado.empty:
                        categorias_counts = df_filtrado[col_categoria].value_counts()
                        
                        fig_bar = px.bar(
                            x=categorias_counts.index,
                            y=categorias_counts.values,
                            color_discrete_sequence=['#1e40af', '#2563eb', '#3b82f6', '#60a5fa']
                        )
                        
                        fig_bar.update_layout(
                            showlegend=False,
                            xaxis_title="División",
                            yaxis_title="Cantidad",
                            height=400
                        )
                        
                        st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.info("No hay datos para mostrar")
                
                with col_grafico2:
                    # Gráfico de Torta por Gravedad
                    st.markdown("#### 🎯 Jugadores por Gravedad")
                    if col_severidad in df_filtrado.columns and not df_filtrado.empty:
                        severidad_counts = df_filtrado[col_severidad].value_counts()
                        
                        fig_pie = px.pie(
                            values=severidad_counts.values,
                            names=severidad_counts.index,
                            color_discrete_sequence=['#22c55e', '#eab308', '#ef4444', '#dc2626']
                        )
                        
                        fig_pie.update_layout(height=400)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.info("No hay datos para mostrar")
                
                st.markdown("---")
                
                # TABLA DE LESIONADOS
                st.markdown("### 👥 Lesionados")
                
                if not df_filtrado.empty:
                    st.success(f"✅ **{len(df_filtrado)} lesionado(s) encontrado(s)**")
                    
                    # Mostrar métricas resumidas
                    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                    with col_met1:
                        st.metric("📋 Total Lesiones", len(df_filtrado))
                    with col_met2:
                        if col_severidad in df_filtrado.columns:
                            leves = len(df_filtrado[df_filtrado[col_severidad].str.contains('Leve', case=False, na=False)])
                            st.metric("🟢 Leves", leves)
                        else:
                            st.metric("🟢 Leves", "N/A")
                    with col_met3:
                        if col_severidad in df_filtrado.columns:
                            moderadas = len(df_filtrado[df_filtrado[col_severidad].str.contains('Moderada', case=False, na=False)])
                            st.metric("🟡 Moderadas", moderadas)
                        else:
                            st.metric("🟡 Moderadas", "N/A")
                    with col_met4:
                        if col_severidad in df_filtrado.columns:
                            graves = len(df_filtrado[df_filtrado[col_severidad].str.contains('Grave', case=False, na=False)])
                            st.metric("🔴 Graves", graves)
                        else:
                            st.metric("🔴 Graves", "N/A")
                    
                    # Tabla de datos
                    st.dataframe(df_filtrado, use_container_width=True, height=400)
                    
                    # Botón para descargar
                    csv = df_filtrado.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar datos filtrados",
                        data=csv,
                        file_name=f"lesiones_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ No se encontraron registros con los filtros seleccionados")
                
            else:
                st.error("❌ No se pudieron cargar los datos")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


# Ejecutar solo si es llamado directamente
if __name__ == "__main__":
    main_streamlit()
    