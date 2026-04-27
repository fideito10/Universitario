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
from src.modules.administracion import JugadoresMaestroManager
from src.utils.credentials import get_credentials_dict

# ==========================================
# GESTIÓN DE CREDENCIALES Y CONEXIÓN
# ==========================================

def get_google_credentials():
    """
    Obtiene las credenciales de Google usando el módulo centralizado.
    """
    return get_credentials_dict()

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
# FUNCIONES DE CONVERSIÓN DE DATOS
# ==========================================

def convertir_valor_a_numero(valor):
    """
    Convierte un valor a número, manejando tanto formatos numéricos como de tiempo.
    
    Formatos soportados:
    - Números decimales: "10.5", "10,5"
    - Tiempos: "5'30''", "6'40''", "5'30\"", "6'40\"" (minutos'segundos)
    
    Returns:
        float: Valor numérico (para tiempos, retorna segundos totales)
        None: Si no se puede convertir
    """
    if pd.isna(valor) or valor == '':
        return None
    
    valor_str = str(valor).strip()
    
    # Detectar formato de tiempo (M'S'' o M'S")
    if "'" in valor_str:
        try:
            # Normalizar: reemplazar comillas dobles (") y comillas simples dobles ('') por espacio
            valor_normalizado = valor_str.replace("''", "").replace('"', "").replace("'", " ")
            partes = valor_normalizado.split()
            
            if len(partes) >= 2:
                minutos = float(partes[0])
                segundos = float(partes[1])
                return minutos * 60 + segundos
            elif len(partes) == 1:
                # Solo minutos
                return float(partes[0]) * 60
        except:
            pass
    
    # Intentar conversión numérica normal
    try:
        return float(valor_str.replace(',', '.'))
    except:
        return None


def formatear_valor_display(valor_original, valor_numerico, unidad):
    """
    Formatea el valor para mostrar, preservando el formato original si es tiempo.
    
    Args:
        valor_original: Valor original del dataframe
        valor_numerico: Valor convertido a número
        unidad: Unidad de medida
    
    Returns:
        str: Valor formateado para mostrar
    """
    if pd.isna(valor_numerico):
        return ""
    
    # Si la unidad es "Tiempo" o el valor original contiene ', mantener formato original
    if unidad == "Tiempo" or "'" in str(valor_original):
        return str(valor_original)
    
    # Para valores numéricos normales
    return f"{valor_numerico:.2f} {unidad}"

def segundos_a_formato_tiempo(segundos_totales):
    """
    Convierte segundos totales a formato M'S"
    
    Args:
        segundos_totales: Número total de segundos (float)
    
    Returns:
        str: Formato M'S" (ejemplo: "3'21\"")
    """
    if pd.isna(segundos_totales):
        return ""
    
    minutos = int(segundos_totales // 60)
    segundos = int(segundos_totales % 60)
    return f"{minutos}'{segundos:02d}\""


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

def mostrar_grafico_top_bottom(df_filtrado, jugador_col, valor_col, test_sel="", subtest_sel="", categoria_sel="", posicion_sel=""):
    """
    Crea visualización de alto impacto mostrando TOP 3 y BOTTOM 3 jugadores en contenedores separados
    """
    if df_filtrado.empty or len(df_filtrado) < 3:
        # No mostrar warning si hay pocos datos, simplemente no renderizar el gráfico grande
        return
    
    # Crear columna auxiliar con valores originales para display
    df_filtrado['valor_original'] = df_filtrado[valor_col]
    
    # Calcular promedio por jugador (usando valores numéricos)
    df_promedio = df_filtrado.groupby(jugador_col).agg({
        valor_col: 'mean',
        'valor_original': 'first'  # Mantener un valor original para referencia
    }).reset_index()
    
    # Obtener unidad
    unidad = df_filtrado['unidad'].iloc[0] if 'unidad' in df_filtrado.columns else ""
    es_tiempo = unidad == "Tiempo"
    
    # Para tiempos, menor es mejor (invertir orden)
    df_promedio = df_promedio.sort_values(valor_col, ascending=es_tiempo)
    
    # Obtener TOP 3 y BOTTOM 3
    top_3 = df_promedio.head(3).copy()
    bottom_3 = df_promedio.tail(3).copy()
    
    # Construir título dinámico
    titulo_test = test_sel.upper() if test_sel else ""
    if subtest_sel and subtest_sel != "":
        titulo_test = f"{titulo_test} ({subtest_sel.upper()})"
        
    filtros_extra = []
    if categoria_sel and categoria_sel != "Todas" and categoria_sel != "":
        filtros_extra.append(categoria_sel)
    if posicion_sel and posicion_sel != "Todas" and posicion_sel != "":
        filtros_extra.append(posicion_sel)
        
    detalle_filtros = f" | {' - '.join(filtros_extra)}" if filtros_extra else ""
    
    st.markdown(f"## 🏆 Máximo rendimiento - {titulo_test}{detalle_filtros}")
    
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
            
            # Obtener el valor original guardado
            jugador_data = df_filtrado[df_filtrado[jugador_col] == row[jugador_col]]
            valor_display = jugador_data['valor_original'].iloc[0] if not jugador_data.empty else row[valor_col]
            
            # DETERMINAR FORMATO DE SALIDA
            valor_display_str = str(valor_display)
            if "'" in valor_display_str:
                # Caso A: Texto original tipo 5'08"
                texto_valor = valor_display_str
            elif unidad == "Tiempo":
                # Caso B: Convertir segundos a formato M'S"
                texto_valor = segundos_a_formato_tiempo(row[valor_col])
            else:
                # Caso C: Valor numérico normal
                texto_valor = f"{row[valor_col]:.2f} {unidad}"
            
            st.markdown(f"""
                <div style='background-color: #E8F5E9; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #2E7D32;'>
                    <strong>{medalla} {row[jugador_col]}</strong><br>
                    <span style='font-size: 1.2em; font-weight: bold; color: #1B5E20;'>{texto_valor}</span>
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
            # Obtener el valor original guardado
            jugador_data = df_filtrado[df_filtrado[jugador_col] == row[jugador_col]]
            valor_display = jugador_data['valor_original'].iloc[0] if not jugador_data.empty else row[valor_col]
            
            # DETERMINAR FORMATO DE SALIDA
            valor_display_str = str(valor_display)
            if "'" in valor_display_str:
                texto_valor = valor_display_str
            elif unidad == "Tiempo":
                texto_valor = segundos_a_formato_tiempo(row[valor_col])
            else:
                texto_valor = f"{row[valor_col]:.2f} {unidad}"
            
            st.markdown(f"""
                <div style='background-color: #FFEBEE; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #C62828;'>
                    <strong>{row[jugador_col]}</strong><br>
                    <span style='font-size: 1.2em; font-weight: bold; color: #B71C1C;'>{texto_valor}</span>
                </div>
            """, unsafe_allow_html=True)

def mostrar_tabla_estilizada(df, valor_col, test_col, subtest_col):
    """
    Muestra una tabla con código de colores según rendimiento vs promedio.
    Versión robusta que maneja errores de visualización y formatos de tiempo.
    """
    if df.empty:
        st.warning("⚠️ No hay datos para mostrar con los filtros seleccionados")
        return
    
    # Obtener unidad del dataframe si existe
    unidad = df['unidad'].iloc[0] if 'unidad' in df.columns else ""
    es_tiempo = unidad == "Tiempo"
    
    
    # 1. Preparar datos
    df_calc = df.copy()
    
    # NOTA: valor_original ya viene guardado desde la función principal (physical_area)
    # No sobrescribir aquí para preservar el formato original de tiempo
    
    # Convertir a numérico (ya está convertido desde la función principal)
    df_calc[valor_col] = pd.to_numeric(df_calc[valor_col], errors='coerce')
    
    # Calcular estadísticas
    promedio = df_calc[valor_col].mean()
    desviacion = df_calc[valor_col].std()
    
    # 2. Configurar visualización
    # Convertir Marca Temporal a tipo fecha para formateo de MM-YYYY
    if 'Marca temporal' in df_calc.columns:
        df_calc['Fecha Test'] = pd.to_datetime(df_calc['Marca temporal'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%m-%Y').fillna("")
    else:
        df_calc['Fecha Test'] = ""
        
    # Mapeo de columnas para renombrar (el orden define la prioridad al elegir columnas)
    cols_map = {
        'Nombre y Apellido': 'Nombre',
        'Posicion': 'Posición',              # Prioridad 1: Viene de la base maestra central
        'Posición del jugador': 'Posición',  # Prioridad 2: Viene de la base Test Físico
        'Categoria': 'Categoría',            # Prioridad 1: Viene de la base maestra central
        'Categoría': 'Categoría'             # Prioridad 2: Viene de la base Test Físico
    }
    
    # Asegurar que las columnas existen, eligiendo solo una por cada destino lógico
    cols_existentes = []
    destinos_agregados = set()
    for source, dest in cols_map.items():
        if source in df_calc.columns and dest not in destinos_agregados:
            cols_existentes.append(source)
            destinos_agregados.add(dest)
    
    # Crear DF para vista incluyendo la columna de valor para el styling y la Fecha
    df_view = df_calc[cols_existentes + [valor_col, 'valor_original', 'Fecha Test']].copy()
    df_view = df_view.rename(columns=cols_map)
    
    # Crear columna de texto formateado "Resultado"
    def formatear_resultado(row):
        if pd.isna(row[valor_col]):
            return ""
        
        # Detectar si el valor original tiene formato de tiempo (contiene ')
        valor_orig_str = str(row['valor_original'])
        if "'" in valor_orig_str:
            # Es un tiempo con formato, mostrar original
            return valor_orig_str
        
        # Si la unidad es "Tiempo", convertir segundos a formato M'S"
        if unidad == "Tiempo":
            return segundos_a_formato_tiempo(row[valor_col])
        
        # Para valores numéricos normales
        return f"{row[valor_col]:.2f} {unidad}"
    
    df_view['Resultado'] = df_view.apply(formatear_resultado, axis=1)
    
    # Como cols_existentes puede tener duplicados lógicos (ej. Categoria y Categoría), filtramos las renombradas finales
    cols_renombradas = [cols_map[c] for c in cols_existentes]
    # Quitamos duplicados manteniendo el orden
    cols_unicas = list(dict.fromkeys(cols_renombradas))
    
    # Reordenar columnas: Solo información deseada
    # Las renombradas primero, luego Resultado, luego Fecha Test, luego columnas auxiliares (ocultas)
    cols_ordenadas = cols_unicas + ['Resultado', 'Fecha Test', valor_col, 'valor_original']
    df_view = df_view[cols_ordenadas]
    
    # Función de estilo
    def aplicar_estilo_fila(row):
        try:
            val = row[valor_col]
            if pd.isna(val) or pd.isna(desviacion) or desviacion == 0:
                return [''] * len(row)
                
            estilo = ''
            
            # Para tiempos, menor es mejor (invertir lógica)
            if es_tiempo:
                if val < promedio - (0.5 * desviacion):
                    # Verde (Mejor que el promedio - menos tiempo)
                    estilo = 'background-color: #C8E6C9; color: #1B5E20'
                elif val > promedio + (0.5 * desviacion):
                    # Rojo (Peor que el promedio - más tiempo)
                    estilo = 'background-color: #FFCDD2; color: #B71C1C'
                else:
                    # Amarillo (Promedio)
                    estilo = 'background-color: #FFF9C4; color: #F57F17'
            else:
                # Para valores numéricos normales, mayor es mejor
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
        
        # Formateo general
        styler.set_properties(**{
            'text-align': 'center',
            'font-family': 'Montserrat, Arial'
        })

        st.dataframe(
            styler,
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                valor_col: None,          # Ocultar visualmente la columna valor
                "valor_original": None    # Ocultar visualmente la columna valor original
            }
        )
    except Exception as e:
        st.error(f"Error al aplicar estilos: {e}")
        # Fallback sin estilos de fila pero funcional
        st.dataframe(
            df_view, 
            use_container_width=True,
            hide_index=True,
            column_config={
                valor_col: None,          # Ocultar visualmente la columna valor
                "valor_original": None    # Ocultar visualmente la columna original
            }
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
    with st.spinner("📊 Cargando datos centralizados..."):
        df_test = cargar_hoja(sheet_id, nombre_hoja)
        admin_manager = JugadoresMaestroManager()
        df_players = admin_manager.get_all_players()
    
    if df_test.empty:
        st.error("❌ No se pudo cargar la hoja 'Base Test'.")
        return
        
    if df_players.empty:
        st.error("❌ No se pudo cargar la base maestra de jugadores.")
        return

    # Limpiar nombres de columnas por posibles espacios
    df_test.columns = df_test.columns.str.strip()
    
    # Asegurar DNI como string para el merge
    col_dni_test = 'Dni' if 'Dni' in df_test.columns else 'DNI' if 'DNI' in df_test.columns else None
    
    if col_dni_test:
        df_test['DNI_merge'] = df_test[col_dni_test].astype(str).str.strip()
    else:
        st.error(f"❌ No se encontró columna DNI en Test Físico. Columnas: {df_test.columns.tolist()}")
        return
        
    df_players['DNI_merge'] = df_players['DNI'].astype(str).str.strip()
    
    # Unificar DataFrames (INNER JOIN para mostrar solo tests de jugadores en BD central)
    df = pd.merge(df_test, df_players, on='DNI_merge', how='inner', suffixes=('_test', '_central'))
    
    # Construir campos combinados y mapear columnas
    df['Nombre y Apellido'] = df['Nombre'].astype(str) + " " + df['Apellido'].astype(str)

    # Definición de Columnas
    categoria_col = "Categoria" # Viene de la base central, sin tilde
    jugador_col = "Nombre y Apellido"
    test_col = "Test"
    subtest_col = "Subtest"
    valor_col = "valor"
    posicion_col = "Posicion" # Viene de la base central, sin tilde

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
    subtest_sel = ""
    if len(subtests) > 0 and any(s != "" for s in subtests):
        subtest_sel = st.selectbox("⚙️ Selecciona el subtest", options=subtests)
        df_final = df_jug[df_jug[subtest_col] == subtest_sel]
    else:
        df_final = df_jug

    # ==========================================
    # PROCESAMIENTO Y VISUALIZACIÓN
    # ==========================================
    
    # Guardar valores originales antes de convertir
    df_final['valor_original'] = df_final[valor_col]
    
    # Convertir valores a números para análisis (maneja tiempos y números)
    df_final[valor_col] = df_final[valor_col].apply(convertir_valor_a_numero)

    if not df_final.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        # 1. Gráfico de Top/Bottom (Pasando el Test y Subtest para el título)
        mostrar_grafico_top_bottom(df_final, jugador_col, valor_col, test_sel, subtest_sel, categoria_sel, posicion_sel)
        
        st.markdown("---")
        
        # 2. Tabla Detallada
        mostrar_tabla_estilizada(df_final, valor_col, test_col, subtest_col)
    else:
        st.info("No hay datos para mostrar con la selección actual.")
