import streamlit as st
import json
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
import gspread
from google.oauth2.service_account import Credentials
import os

# ==========================================
# GESTIÓN DE CREDENCIALES Y CONEXIÓN
# ==========================================

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
            "credentials/service_account.json",
            "../credentials/service_account.json", 
            "C:/Users/dell/Desktop/Car/credentials/service_account.json"
        ]
        
        for cred_path in possible_paths:
            if os.path.exists(cred_path):
                with open(cred_path) as f:
                    return json.load(f)
        
        raise FileNotFoundError("No se encontró archivo de credenciales")
        
    except Exception as e:
        st.error(f"❌ Error cargando credenciales: {e}")
        return None

def cargar_hoja(sheet_id: str, nombre_hoja: str, rutas_credenciales=None) -> pd.DataFrame:
    """
    Carga una hoja de Google Sheets usando el sheet_id y el nombre de la pestaña.
    """
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        # Obtener credenciales usando la función mejorada
        creds_info = get_google_credentials()
        
        if creds_info is None:
            st.error("❌ No se pudieron cargar las credenciales de Google")
            return pd.DataFrame()
        
        # Crear credenciales desde la información obtenida
        credenciales = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        
        gc = gspread.authorize(credenciales)
        sh = gc.open_by_key(sheet_id)
        
        # Obtener todas las pestañas para diagnóstico y búsqueda flexible
        todas_las_hojas = sh.worksheets()
        nombres_hojas = [h.title for h in todas_las_hojas]
        
        worksheet = None
        
        # 1. Intentar por nombre exacto
        try:
            worksheet = sh.worksheet(nombre_hoja)
        except:
            # 2. Intentar búsqueda flexible (sin espacios, sin mayúsculas/minúsculas)
            busqueda = nombre_hoja.strip().lower().replace(" ", "")
            for h in todas_las_hojas:
                if h.title.strip().lower().replace(" ", "") == busqueda:
                    worksheet = h
                    break
            
            # 3. Si sigue sin aparecer, intentar por índice 0
            if not worksheet and todas_las_hojas:
                worksheet = todas_las_hojas[0]
        
        if not worksheet:
            raise Exception(f"No se encontró la pestaña '{nombre_hoja}'. Pestañas disponibles: {nombres_hojas}")
        
        all_data = worksheet.get_all_values()
        return pd.DataFrame(all_data[1:], columns=all_data[0]) if all_data else pd.DataFrame()

    except gspread.exceptions.SpreadsheetNotFound:
        st.error("❌ Google Sheet no encontrado. Verifica el ID y permisos.")
        return pd.DataFrame()
        
    except gspread.exceptions.APIError as e:
        st.error(f"❌ Error de API: {e}. Verifica que hayas compartido el sheet con la cuenta de servicio.")
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Error al cargar la hoja: {e}")
        return pd.DataFrame()

# ==========================================
# FUNCIONES DE VISUALIZACIÓN Y ESTILO
# ==========================================

def resaltar_valores(s):
    """
    Genera estilos CSS condicionales para una serie de datos
    """
    # Reemplaza coma por punto y convierte a float
    s_float = pd.to_numeric(s.astype(str).str.replace(',', '.'), errors='coerce')
    is_high = s_float > s_float.quantile(0.75)
    is_low = s_float < s_float.quantile(0.25)
    return ['background-color: #b6fcd5' if h else 'background-color: #ffb6b6' if l else '' for h, l in zip(is_high, is_low)]

def mostrar_grafico_top_bottom(df_filtrado, jugador_col, valor_col):
    """
    Crea visualización de alto impacto mostrando TOP 3 y BOTTOM 3 jugadores en contenedores separados
    """
    if df_filtrado.empty or len(df_filtrado) < 3:
        # No mostrar warning si hay pocos datos, simplemente no renderizar el gráfico grande
        return
    
    # Calcular promedio por jugador
    df_promedio = df_filtrado.groupby(jugador_col)[valor_col].mean().reset_index()
    df_promedio = df_promedio.sort_values(valor_col, ascending=False)
    
    # Obtener TOP 3 y BOTTOM 3
    top_3 = df_promedio.head(3).copy()
    bottom_3 = df_promedio.tail(3).copy()
    
    # Obtener nombre del test y unidad
    nombre_test = df_filtrado['Test'].iloc[0] if 'Test' in df_filtrado.columns else "Test"
    unidad = df_filtrado['unidad'].iloc[0] if 'unidad' in df_filtrado.columns else ""
    
    st.markdown(f"## 🏆 Top Rendimiento - {nombre_test}")
    
    col_top, col_bottom = st.columns(2)
    
    # ============= CONTENEDOR TOP 3 =============
    with col_top:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 150%); 
                        padding: 15px; 
                        border-radius: 10px; 
                        margin-bottom: 20px;
                        color: white;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='margin:0;'>🔥 MEJORES RESULTADOS</h3>
            </div>
        """, unsafe_allow_html=True)
        
        for idx, (_, row) in enumerate(top_3.iterrows(), 1):
            medalla = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉"
            st.markdown(f"""
                <div style='background-color: #E8F5E9; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #2E7D32;'>
                    <strong>{medalla} {row[jugador_col]}</strong><br>
                    <span style='font-size: 1.2em; font-weight: bold; color: #1B5E20;'>{row[valor_col]:.2f} {unidad}</span>
                </div>
            """, unsafe_allow_html=True)
    
    # ============= CONTENEDOR BOTTOM 3 =============
    with col_bottom:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #B71C1C 0%, #C62828 100%); 
                        padding: 15px; 
                        border-radius: 10px; 
                        margin-bottom: 20px;
                        color: white;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='margin:0;'>⚠️ ZONA DE MEJORA</h3>
            </div>
        """, unsafe_allow_html=True)
        
        for idx, (_, row) in enumerate(bottom_3.iloc[::-1].iterrows(), 1):
             st.markdown(f"""
                <div style='background-color: #FFEBEE; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #C62828;'>
                    <strong>{row[jugador_col]}</strong><br>
                    <span style='font-size: 1.2em; font-weight: bold; color: #B71C1C;'>{row[valor_col]:.2f} {unidad}</span>
                </div>
            """, unsafe_allow_html=True)

def mostrar_tabla_estilizada(df, valor_col, test_col, subtest_col):
    """
    Muestra una tabla con código de colores según rendimiento vs promedio.
    Versión robusta que maneja errores de visualización.
    """
    if df.empty:
        st.warning("⚠️ No hay datos para mostrar con los filtros seleccionados")
        return
    
    # Obtener unidad del dataframe si existe
    unidad = df['unidad'].iloc[0] if 'unidad' in df.columns else ""
    
    # 1. Preparar datos y asegurar tipos numéricos
    df_calc = df.copy()
    df_calc[valor_col] = pd.to_numeric(df_calc[valor_col], errors='coerce')
    
    # Calcular estadísticas
    promedio = df_calc[valor_col].mean()
    desviacion = df_calc[valor_col].std()
    
    # 2. Configurar visualización
    # Mapeo de columnas para renombrar
    cols_map = {
        'Nombre y Apellido': 'Nombre',
        'Posición del jugador': 'Posición',
        'Categoría': 'Categoría'
    }
    
    # Asegurar que las columnas existen
    cols_existentes = [c for c in cols_map.keys() if c in df_calc.columns]
    
    # Crear DF para vista incluyendo la columna de valor para el styling
    df_view = df_calc[cols_existentes + [valor_col]].copy()
    df_view = df_view.rename(columns=cols_map)
    
    # Crear columna de texto formateado "Resultado"
    df_view['Resultado'] = df_view[valor_col].apply(
        lambda x: f"{x:.2f} {unidad}" if pd.notna(x) else ""
    )
    
    # Reordenar columnas: Las renombradas primero, luego Resultado, luego valor (oculto)
    cols_ordenadas = [cols_map[c] for c in cols_existentes] + ['Resultado', valor_col]
    df_view = df_view[cols_ordenadas]
    
    # Mostrar estadísticas como métricas antes de la tabla
    c1, c2, c3 = st.columns(3)
    c1.metric("Promedio", f"{promedio:.2f} {unidad}")
    if not pd.isna(desviacion):
        c2.metric("Desviación Estándar", f"{desviacion:.2f}")
    
    # Función de estilo
    def aplicar_estilo_fila(row):
        try:
            val = row[valor_col]
            if pd.isna(val) or pd.isna(desviacion) or desviacion == 0:
                return [''] * len(row)
                
            estilo = ''
            if val > promedio + (0.5 * desviacion):
                # Verde (Encima del promedio)
                estilo = 'background-color: #C8E6C9; color: #1B5E20'
            elif val < promedio - (0.5 * desviacion):
                # Rojo (Debajo del promedio)
                estilo = 'background-color: #FFCDD2; color: #B71C1C'
            else:
                # Amarillo (Promedio)
                estilo = 'background-color: #FFF9C4; color: #F57F17'
                
            return [estilo] * len(row)
        except Exception:
            return [''] * len(row)

    st.markdown("### 📋 Tabla de Resultados")
    
    # Leyenda
    st.markdown("""
        <div style='display: flex; gap: 15px; margin-bottom: 10px; font-size: 0.9em;'>
            <span style='background-color: #C8E6C9; padding: 2px 8px; border-radius: 4px; color: #1B5E20'><b>Verde:</b> > Promedio</span>
            <span style='background-color: #FFF9C4; padding: 2px 8px; border-radius: 4px; color: #F57F17'><b>Amarillo:</b> Promedio</span>
            <span style='background-color: #FFCDD2; padding: 2px 8px; border-radius: 4px; color: #B71C1C'><b>Rojo:</b> < Promedio</span>
        </div>
    """, unsafe_allow_html=True)

    try:
        # Aplicar estilo
        styler = df_view.style.apply(aplicar_estilo_fila, axis=1)
        
        # Ocultar columna auxiliar 'valor' de forma compatible
        if hasattr(styler, "hide"):
            styler.hide(subset=[valor_col], axis=1, names=False) # names=False oculta header tb si es necesario en pandas nuevos
        elif hasattr(styler, "hide_columns"):
            styler.hide_columns([valor_col])
            
        # Formateo general
        styler.set_properties(**{
            'text-align': 'center',
            'font-family': 'Montserrat, Arial'
        })

        st.dataframe(
            styler,
            use_container_width=True,
            hide_index=True,
            height=500
        )
    except Exception as e:
        st.error(f"Error al aplicar estilos: {e}")
        # Fallback sin estilos de fila pero funcional
        st.dataframe(
            df_view.drop(columns=[valor_col]), 
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# FUNCIÓN PRINCIPAL DEL MÓDULO
# ==========================================

def physical_area():
    # Header Branding (Universitario)
    st.markdown("""
        <link href="https://fonts.googleapis.com/css?family=Montserrat:400,700&display=swap" rel="stylesheet">
        <style>
        html, body, [class*="css"] {
            font-family: 'Montserrat', Arial, sans-serif !important;
        }
        .titulo-area-fisica {
            background: #000000;
            color: #fff;
            border-radius: 16px;
            padding: 32px 0 16px 0;
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 16px;
        }
        .subtitulo-area-fisica {
            text-align: center;
            color: #212529;
            font-size: 1.2em;
            font-weight: 500;
        }
        </style>
        <div class='titulo-area-fisica'>
            🏋️ ÁREA FÍSICA
        </div>
        <div class='subtitulo-area-fisica'>
            Sistema de Análisis Físico - Club Universitario de La Plata
        </div>
        <hr style='border: 1px solid #000000;'>
    """, unsafe_allow_html=True)
    
    # ID de Google Sheet (Universitario)
    sheet_id = "1sR4wWsA0_nZGS011d6QV84znTnRW4d7iS65y2oBjvYI"
    nombre_hoja = "Base Test"
    
    # Cargar datos
    with st.spinner("📊 Cargando datos desde Google Sheets..."):
        df = cargar_hoja(sheet_id, nombre_hoja)
    
    if df.empty:
        st.error("❌ No se pudo cargar la hoja 'Base Test'.")
        return

    # Definición de Columnas
    categoria_col = "Categoría"
    jugador_col = "Nombre y Apellido"
    test_col = "Test"
    subtest_col = "Subtest"
    valor_col = "valor"
    posicion_col = "Posición del jugador"

    # ==========================================
    # SISTEMA DE FILTROS CASCADA
    # ==========================================
    st.markdown("### 🔎 Filtros Interactivos")
    
    # 1. Categoría
    categorias = sorted(df[categoria_col].dropna().unique())
    categoria_sel = st.selectbox("📂 Selecciona la categoría", options=categorias)
    df_cat = df[df[categoria_col] == categoria_sel]

    # 2. Test
    tests = sorted(df_cat[test_col].dropna().unique())
    test_sel = st.selectbox("🏃 Selecciona el test físico", options=tests)
    df_test = df_cat[df_cat[test_col] == test_sel]

    # 3. Grupo y Posición (Layout de columnas)
    col_grupo, col_pos = st.columns(2)
    
    # Definición de Grupos de Rugby
    FORWARDS = ["Pilar", "Hooker", "Segunda Linea", "Segunda Línea", "Tercera Linea", "Tercera Línea", "Octavo", "Pilar Izquierdo", "Pilar Derecho"]
    BACKS = ["Medio Scrum", "Apertura", "Centro", "Wing", "Fullback"]
    
    with col_grupo:
        grupo_sel = st.radio(
            "⚡ Selecciona el grupo",
            ["Todos", "Forwards", "Backs"],
            horizontal=True
        )

    # Filtrar dataframe por grupo
    if grupo_sel == "Forwards":
        # Filtrado flexible (case insensitive y parcial)
        df_grupo = df_test[df_test[posicion_col].astype(str).str.lower().apply(lambda x: any(f.lower() in x for f in FORWARDS))]
    elif grupo_sel == "Backs":
        df_grupo = df_test[df_test[posicion_col].astype(str).str.lower().apply(lambda x: any(b.lower() in x for b in BACKS))]
    else:
        df_grupo = df_test

    with col_pos:
        # Obtener posiciones disponibles en el grupo filtrado
        posiciones_disponibles = sorted(df_grupo[posicion_col].astype(str).unique())
        posicion_sel = st.selectbox("🎯 Selecciona la posición específica", options=["Todas"] + posiciones_disponibles)

    # Filtrar dataframe por posición
    if posicion_sel != "Todas":
        df_pos = df_grupo[df_grupo[posicion_col] == posicion_sel]
    else:
        df_pos = df_grupo

    # 4. Jugadores
    jugadores = sorted(df_pos[jugador_col].dropna().unique())
    st.caption(f"🔍 {len(jugadores)} jugadores disponibles en esta selección")
    
    jugadores_sel = st.multiselect("👤 Selecciona jugador/es", options=jugadores)

    if jugadores_sel:
        df_jug = df_pos[df_pos[jugador_col].isin(jugadores_sel)]
    else:
        df_jug = df_pos

    # 5. Subtest (si aplica)
    subtests = sorted(df_jug[subtest_col].dropna().unique())
    if len(subtests) > 0 and subtests[0] != "":
        subtest_sel = st.selectbox("⚙️ Selecciona el subtest", options=subtests)
        df_final = df_jug[df_jug[subtest_col] == subtest_sel]
    else:
        df_final = df_jug

    # ==========================================
    # PROCESAMIENTO Y VISUALIZACIÓN
    # ==========================================
    
    # Convertir valores a números para análisis
    df_final[valor_col] = df_final[valor_col].astype(str).str.replace(',', '.')
    df_final[valor_col] = pd.to_numeric(df_final[valor_col], errors='coerce')

    if not df_final.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        # 1. Gráfico de Top/Bottom
        mostrar_grafico_top_bottom(df_final, jugador_col, valor_col)
        
        st.markdown("---")
        
        # 2. Tabla Detallada
        mostrar_tabla_estilizada(df_final, valor_col, test_col, subtest_col)
    else:
        st.info("No hay datos para mostrar con la selección actual.")
