import streamlit as st
import pandas as pd
import os
import sys
import re
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Importaciones de otros módulos
try:
    from .areamedica import read_google_sheet_with_headers, create_dataframe_from_sheet
except ImportError:
    read_google_sheet_with_headers = None
    create_dataframe_from_sheet = None

try:
    from .areanutricion import read_google_sheet_as_df
except ImportError:
    read_google_sheet_as_df = None

def filtrar_ultimo_registro_por_jugador(df):
    """Filtra el último registro para cada jugador basado en DNI y Marca temporal"""
    if df is None or df.empty:
        return df
    
    col_dni = buscar_columna_dni(df)
    
    # Buscar columna de fecha
    col_fecha = None
    for c in ['Marca temporal', 'Fecha', 'fecha', 'Timestamp']:
        if c in df.columns:
            col_fecha = c
            break
            
    if col_dni and col_fecha:
        df_copy = df.copy()
        try:
            df_copy[col_dni] = df_copy[col_dni].apply(normalizar_dni)
            df_copy[col_fecha] = pd.to_datetime(df_copy[col_fecha], errors='coerce')
            # Ordenar por fecha y tomar el último
            return df_copy.sort_values(col_fecha).groupby(col_dni).tail(1)
        except:
            return df
    return df

try:
    from .areafisica import cargar_hoja
except ImportError:
    cargar_hoja = None

try:
    from .administracion import JugadoresMaestroManager
except ImportError:
    JugadoresMaestroManager = None

def obtener_df_central():
    """Obtiene el DataFrame de la Base Central (Jugadores Maestro) de Universitario"""
    try:
        if not JugadoresMaestroManager:
            return pd.DataFrame()
        manager = JugadoresMaestroManager()
        df_central = manager.get_all_players()
        if not df_central.empty:
            # Estandarizar nombres para Universitario
            if 'Nombre' in df_central.columns and 'Apellido' in df_central.columns:
                df_central['Nombre y Apellido'] = df_central['Nombre'].astype(str).str.strip() + ' ' + df_central['Apellido'].astype(str).str.strip()
            df_central['origen_modulo'] = 'central'
            return df_central
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def obtener_df_medica():
    """Obtiene el DataFrame del área médica"""
    try:
        if not read_google_sheet_with_headers: return pd.DataFrame()
        result = read_google_sheet_with_headers(sheet_id="1ham2WSMQa3eEv0V0TtHcAa55R3WLGoBje6pSOoNxcBQ")
        if result and isinstance(result, dict) and result.get('success'):
            df = pd.DataFrame(result['data'])
            if not df.empty:
                df['origen_modulo'] = 'medica'
                return df
        return pd.DataFrame()
    except Exception: return pd.DataFrame()

def obtener_df_nutricion():
    """Obtiene el DataFrame del área de nutrición (historial completo)"""
    try:
        if not read_google_sheet_as_df: return pd.DataFrame()
        df = read_google_sheet_as_df(sheet_id='1CpAklgxgcVJrIWRWt-yJW4u6EkTcIeQqqp87kllsUqo', worksheet_name="Respuestas de formulario 1")
        if df is not None and not df.empty:
            # IMPORTANTE: No filtramos el último aquí para que el historial esté disponible
            # para buscar datos faltantes (ej: talla no cargada en el último control)
            df['origen_modulo'] = 'nutricion'
            return df
        return pd.DataFrame()
    except Exception: return pd.DataFrame()

def obtener_df_fisica():
    """Obtiene el DataFrame del área física usando el ID de Universitario"""
    try:
        if not cargar_hoja: return pd.DataFrame()
        sheet_id = "1sR4wWsA0_nZGS011d6QV84znTnRW4d7iS65y2oBjvYI"
        df = cargar_hoja(sheet_id, "Base Test")
        if df is not None and not df.empty:
            df['origen_modulo'] = 'fisica'
            return df
        return pd.DataFrame()
    except Exception: return pd.DataFrame()

def buscar_columna_jugador(df):
    """Busca columna de nombre estandarizada"""
    for col in ['Nombre y Apellido', 'Nombre completo del jugador', 'Jugador', 'Nombre', 'nombre']:
        if col in df.columns: return col
    return None

def normalizar_dni(dni):
    """Limpia y normaliza el DNI para asegurar coincidencias entre módulos.
    Elimina puntos, comas y maneja el caso de .0 al final de strings numericos."""
    if pd.isna(dni) or str(dni).strip() == "" or str(dni).strip().lower() == "nan": 
        return ""
    
    # Convertir a string
    s = str(dni).strip()
    
    # Manejar caso de float convertido a string (ej: 12345678.0)
    if s.endswith('.0'):
        s = s[:-2]
        
    # Eliminar cualquier carácter no numérico (puntos, comas, espacios)
    import re
    s = re.sub(r'\D', '', s)
    return s

def buscar_columna_dni(df):
    """Busca columna de DNI estandarizada con limpieza de espacios"""
    # Limpiar nombres de columnas para la búsqueda
    cols_map = {str(c).strip().lower(): c for c in df.columns}
    posibles = ['dni', 'documento', 'por favor completa el dni', 'nro dni', 'cedula']
    
    for p in posibles:
        if p in cols_map:
            return cols_map[p]
    
    # Fallback clásico
    for col in ['DNI', 'Dni', 'dni', 'Por Favor completa el Dni', 'documento']:
        if col in df.columns: return col
    return None

def buscar_columna_categoria(df):
    """Busca columna de categoría estandarizada"""
    for col in ['Categoria', 'Categoría', 'categoria', 'division', 'plantel']:
        if col in df.columns: return col
    return None

def normalizar_valor_numerico(valor):
    """Convierte valores de forma ultra-robusta. 
    Maneja '82,1', '82.1', y corrige errores de decimales perdidos."""
    if pd.isna(valor) or str(valor).strip() in ["", "None", "nan"]: return None
    try:
        # Convertir a string para limpieza uniforme
        s = str(valor).lower().replace('kg', '').replace('cm', '').strip()
        
        # Manejo de comas y puntos (formato AR: 83,1)
        if ',' in s:
            if '.' in s and s.find('.') < s.find(','): # Punto de miles
                s = s.replace('.', '')
            s = s.replace(',', '.')
        
        val = float(s)
        
        # CORRECCIÓN DE "831.0" -> "83.1"
        # Si el valor es irracional para un peso (ej: > 250), dividimos por 10.
        if val > 250:
            val = val / 10.0
                
        return round(val, 1)
    except:
        return None

def buscar_columna_flexible(df, palabras_clave):
    """Busca una columna que contenga todas las palabras clave (case insensitive)"""
    for col in df.columns:
        col_lower = str(col).lower()
        if all(kw.lower() in col_lower for kw in palabras_clave):
            return col
    return None

# Elimino el cache temporalmente para asegurar que veas los datos reales sin errores viejos
# @st.cache_data
def crear_dataframe_integrado():
    """Combina los datos usando la Base Central de Universitario como fuente de verdad"""
    df_central = obtener_df_central()
    if df_central.empty:
        st.warning("⚠️ La Base Central de Universitario está vacía. Registre jugadores primero.")
        return pd.DataFrame()

    df_medica = obtener_df_medica()
    df_nutricion = obtener_df_nutricion()
    df_fisica = obtener_df_fisica()
    
    col_dni_central = buscar_columna_dni(df_central)
    col_nom_central = buscar_columna_jugador(df_central)
    col_cat_central = buscar_columna_categoria(df_central)
    
    # Limpieza profunda de la Base Central
    df_central[col_dni_central] = df_central[col_dni_central].apply(normalizar_dni)
    if col_nom_central:
        df_central[col_nom_central] = df_central[col_nom_central].astype(str).str.strip()
    if col_cat_central:
        df_central[col_cat_central] = df_central[col_cat_central].astype(str).str.strip()
    
    # Mapas de la Base Central para normalizar todos los registros
    mapeo_nombres = dict(zip(df_central[col_dni_central], df_central[col_nom_central]))
    mapeo_categorias = {}
    if col_cat_central:
        mapeo_categorias = dict(zip(df_central[col_dni_central], df_central[col_cat_central]))
    
    dni_validos = set(df_central[col_dni_central].tolist())

    # Solo incluimos registros cuyos DNIs existan en Universitario
    registros_finales = [df_central]
    for df_mod in [df_medica, df_nutricion, df_fisica]:
        if not df_mod.empty:
            c_dni = buscar_columna_dni(df_mod)
            c_nom = buscar_columna_jugador(df_mod)
            c_cat = buscar_columna_categoria(df_mod)
            
            if c_dni:
                df_mod[c_dni] = df_mod[c_dni].apply(normalizar_dni)
                
                # Estandarizar nombres y categorías en el módulo también
                if c_nom: df_mod[c_nom] = df_mod[c_nom].astype(str).str.strip()
                
                # Intentar filtrar por DNI
                df_filtrado = df_mod[df_mod[c_dni].isin(dni_validos)].copy()
                
                # Si no hubo coincidencia por DNI, intentar por Nombre (Fallback)
                if df_filtrado.empty and c_nom:
                    nombres_registrados_lower = set(str(n).lower().strip() for n in df_central[col_nom_central])
                    df_filtrado = df_mod[df_mod[c_nom].str.lower().str.strip().isin(nombres_registrados_lower)].copy()
                
                if not df_filtrado.empty:
                    # NORMALIZACIÓN CRÍTICA: Unificar nombres de columnas de identidad
                    # 1. Normalizar DNI
                    df_filtrado[col_dni_central] = df_filtrado[c_dni]
                    
                    # 2. Normalizar Nombre (usar el de la Central)
                    df_filtrado[col_nom_central] = df_filtrado[col_dni_central].map(mapeo_nombres)
                    
                    # 3. Normalizar Categoría (usar la de la Central)
                    if col_cat_central:
                        df_filtrado[col_cat_central] = df_filtrado[col_dni_central].map(mapeo_categorias)
                    
                    # Limpiar columnas duplicadas si los nombres eran distintos
                    columnas_a_mantener = [c for c in df_filtrado.columns if c not in [c_dni, c_nom, c_cat] or c in [col_dni_central, col_nom_central, col_cat_central]]
                    registros_finales.append(df_filtrado[columnas_a_mantener])

    return pd.concat(registros_finales, ignore_index=True, sort=False)

def obtener_categorias_disponibles(df_combinado):
    """Obtiene las categorías reales de Universitario"""
    col = buscar_columna_categoria(df_combinado)
    if col:
        # Usar set para evitar duplicados y ordenar
        cats = sorted(list(set(
            str(c).strip() for c in df_combinado[col].dropna().unique() 
            if str(c).strip() not in ['12', 'nan', 'None', '', '0']
        )))
        return (['Todos los jugadores'] + cats), col
    return ['Todos los jugadores'], None


def mostrar_foto_jugador(nombre_jugador, dni_jugador):
    """
    Busca y muestra la foto del jugador.
    Prioridad de búsqueda:
    1. src/assets/fotos_jugadores/[DNI].jpg (o png, jpeg, webp)
    2. src/assets/fotos_jugadores/[NOMBRE].jpg (o png, jpeg, webp)
    3. Placeholder
    """
    import os
    
    # Definir rutas posibles
    base_dirs = [
        os.path.join(os.getcwd(), 'src', 'assets', 'fotos_jugadores'),
        os.path.join(os.getcwd(), 'assets', 'fotos_jugadores'), # Fallback por si corre desde src
        r"C:\Users\dell\Desktop\Universitario\src\assets\fotos_jugadores" # Ruta absoluta hardcoded por seguridad
    ]
    
    # Extensiones soportadas
    extensions = ['.jpg', '.jpeg', '.png', '.webp']
    
    foto_path = None
    
    # Normalizar datos para búsqueda
    dni_limpio = str(dni_jugador).strip().replace('.', '') if dni_jugador else None
    nombre_limpio = str(nombre_jugador).strip() if nombre_jugador else None
    
    # Estrategia de búsqueda
    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            continue
            
        # 1. Buscar por DNI (Prioridad máxima)
        if dni_limpio:
            for ext in extensions:
                p = os.path.join(base_dir, f"{dni_limpio}{ext}")
                if os.path.exists(p):
                    foto_path = p
                    break
        
        if foto_path: break
        
        # 2. Buscar por Nombre completo
        if nombre_limpio:
            for ext in extensions:
                p = os.path.join(base_dir, f"{nombre_limpio}{ext}")
                if os.path.exists(p):
                    foto_path = p
                    break
        
        if foto_path: break

    # Renderizar Imagen o Placeholder
    if foto_path:
        try:
            return st.image(foto_path, width=200)
        except:
            pass # Si falla, caer en placeholder

    # Placeholder por defecto
    return st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <div style="
            width: 200px; 
            height: 200px; 
            border-radius: 15px; 
            border: 4px solid #000000;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        ">
            <div style="font-size: 4rem; color: #000000;">👤</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    

def cargar_estilos_profesionales():
    """Cargar estilos CSS profesionales para el club de rugby Universitario (Negro y Blanco)"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --rugby-primary: #000000;
        --rugby-secondary: #2d2d2d;
        --rugby-accent: #4a4a4a;
        --rugby-light: #f8f9fa;
        --rugby-success: #28a745;
        --rugby-warning: #ffc107;
        --rugby-danger: #dc3545;
        --rugby-neutral: #6c757d;
    }
    
    .main-panel {
        background: linear-gradient(135deg, var(--rugby-light) 0%, #ffffff 100%);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    
    .player-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        border-left: 10px solid var(--rugby-primary);
        margin-bottom: 1rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, var(--rugby-primary) 0%, var(--rugby-secondary) 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .stat-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: white;
    }
    
    .stat-card p {
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.9;
        color: white;
    }
    
    .module-tab {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    .player-photo {
        border-radius: 15px;
        border: 4px solid var(--rugby-primary);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        width: 100%;
        max-width: 250px;
    }
    
    .info-badge {
        background: var(--rugby-light);
        color: var(--rugby-primary);
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.2rem;
        display: inline-block;
        border: 1px solid #dee2e6;
    }
    
    .status-available {
        background: var(--rugby-success);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .status-injured {
        background: var(--rugby-danger);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.8rem 0;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .metric-label {
        font-weight: 500;
        color: var(--rugby-neutral);
    }
    
    .metric-value {
        font-weight: 700;
        color: var(--rugby-primary);
        font-size: 1.1rem;
    }
    
    .section-title {
        color: var(--rugby-primary);
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 2px solid var(--rugby-accent);
        padding-bottom: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: var(--rugby-light);
        border-radius: 10px;
        color: var(--rugby-primary);
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--rugby-primary);
        color: white;
        border-bottom: 2px solid white;
    }
    
    /* Responsive Design para Panel 360 */
    @media (max-width: 768px) {
        .main-panel {
            padding: 1rem;
        }
        
        /* Ajustar header del panel */
        div[style*="background: linear-gradient"] h1 {
            font-size: 1.5rem !important;
        }
        div[style*="background: linear-gradient"] p {
            font-size: 0.9rem !important;
        }
        div[style*="width: 80px"] {
            width: 60px !important;
            height: 60px !important;
            font-size: 1.8rem !important;
        }
        
        /* Ajustar tarjetas de estadísticas */
        .stat-card h3 {
            font-size: 1.5rem;
        }
        
        /* Ajustes de columnas que se vuelven filas */
        .metric-row {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.2rem;
        }
        
        .section-title {
            font-size: 1.1rem;
        }
        
        /* Ajustar foto del jugador */
        .player-photo {
            max-width: 150px;
            margin: 0 auto 1rem auto;
            display: block;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def obtener_jugadores_por_categoria(df_combinado, categoria_seleccionada, col_categoria):
    """Obtiene jugadores filtrados por categoría con DNI como identificador único"""
    col_jugador = buscar_columna_jugador(df_combinado)
    col_dni = buscar_columna_dni(df_combinado)
    
    if not col_jugador:
        return []
    
    # Filtrar por categoría
    if col_categoria and categoria_seleccionada != 'Todos los jugadores':
        # Asegurar que la comparación sea contra strings limpios
        df_filtrado = df_combinado[df_combinado[col_categoria].astype(str).str.strip() == str(categoria_seleccionada).strip()]
    else:
        df_filtrado = df_combinado
    
    # Crear lista de jugadores únicos por DNI
    jugadores_unicos = {}
    
    for _, fila in df_filtrado.iterrows():
        nombre = fila[col_jugador] if pd.notna(fila[col_jugador]) else None
        dni = fila[col_dni] if col_dni and pd.notna(fila[col_dni]) else None
        
        if nombre and dni:
            # Usar DNI como clave única
            clave_unica = str(dni)
            if clave_unica not in jugadores_unicos:
                # Formato: "Nombre y Apellido (DNI: 12345678)"
                jugadores_unicos[clave_unica] = f"{nombre} (DNI: {dni})"
    
    # Retornar lista ordenada de jugadores con formato nombre + DNI
    return sorted(jugadores_unicos.values())

def extraer_dni_de_seleccion(jugador_seleccionado):
    """Extrae el DNI del formato 'Nombre y Apellido (DNI: 12345678)'"""
    try:
        # Buscar el patrón "(DNI: número)"
        import re
        match = re.search(r'\(DNI: (\d+)\)', jugador_seleccionado)
        if match:
            return match.group(1)
    except:
        pass
    return None

def obtener_datos_jugador(df_combinado, jugador_seleccionado):
    """Obtiene todos los datos de un jugador específico usando DNI como identificador único"""
    col_dni = buscar_columna_dni(df_combinado)
    
    if not col_dni:
        # Si no hay DNI, usar el método anterior por nombre
        col_jugador = buscar_columna_jugador(df_combinado)
        if not col_jugador:
            return pd.DataFrame()
        datos_jugador = df_combinado[df_combinado[col_jugador] == jugador_seleccionado]
        return datos_jugador
    
    # Extraer DNI del formato seleccionado
    dni_jugador = normalizar_dni(extraer_dni_de_seleccion(jugador_seleccionado))
    
    if not dni_jugador:
        return pd.DataFrame()
    
    # Buscar por DNI (identificador único)
    datos_jugador = df_combinado[df_combinado[col_dni].apply(normalizar_dni) == dni_jugador]
    return datos_jugador



def mostrar_ficha_personal_simple(datos_jugador):
    """Muestra la ficha personal del jugador usando solo componentes nativos de Streamlit"""
    if datos_jugador.empty:
        st.warning("No se encontraron datos del jugador")
        return
    
    # Obtener datos básicos usando las columnas exactas del CAR
    jugador_nombre = None
    dni = None
    categoria = None
    posicion = None
    peso = None
    altura = None
    
    # Buscar en todas las filas del jugador para obtener la información más completa
    for _, fila in datos_jugador.iterrows():
        # Nombre del jugador
        if pd.notna(fila.get('Nombre completo del jugador')):
            jugador_nombre = fila['Nombre completo del jugador']
        elif pd.notna(fila.get('Nombre y Apellido')):
            jugador_nombre = fila['Nombre y Apellido']
        elif pd.notna(fila.get('Nombre')) and pd.notna(fila.get('Apellido')):
            jugador_nombre = f"{fila['Nombre']} {fila['Apellido']}"
        
        # DNI
        if pd.notna(fila.get('DNI')):
            dni = fila['DNI']
        elif pd.notna(fila.get('Dni')):
            dni = fila['Dni']
        elif pd.notna(fila.get('Por Favor completa el Dni')):
            dni = fila['Por Favor completa el Dni']
        
        # Categoría
        if pd.notna(fila.get('Categoria')):
            categoria = fila['Categoria']
        elif pd.notna(fila.get('Categoría')):
            categoria = fila['Categoría']
        
        # Posición
        if pd.notna(fila.get('Posicion')):
            posicion = fila['Posicion']
        elif pd.notna(fila.get('Posición del jugador')):
            posicion = fila['Posición del jugador']
        elif pd.notna(fila.get('Posición')):
            posicion = fila['Posición']
    
    # DETERMINACIÓN DE PESO Y ALTURA (BÚSQUEDA EXHAUSTIVA)
    # Buscamos en TODOS los registros del jugador, priorizando Nutrición
    # Columnas probables para cada métrica
    cols_peso = [c for c in datos_jugador.columns if 'peso' in str(c).lower()]
    cols_talla = [c for c in datos_jugador.columns if any(p in str(c).lower() for p in ['talla', 'altura', 'estatura'])]
    
    # Prioridad: Registros de nutrición ordenados por fecha
    datos_buscar = datos_jugador.sort_index(ascending=False)
    
    for _, fila in datos_buscar.iterrows():
        # Peso
        if peso is None:
            # 1. Intentar columnas conocidas de nutrición
            for c in ['Peso (kg): [Número con decimales 88,5]', 'Peso']:
                val = normalizar_valor_numerico(fila.get(c))
                if val and val > 0: 
                    peso = val
                    break
            # 2. Intentar cualquier columna que diga "peso"
            if peso is None:
                for c in cols_peso:
                    val = normalizar_valor_numerico(fila.get(c))
                    if val and val > 0:
                        peso = val
                        break
        
        # Altura
        if altura is None:
            # 1. Prioridad absoluta a "Talla (cm): [Número]" o "Talla"
            for c in ['Talla (cm): [Número]', 'Talla', 'Altura']:
                val = normalizar_valor_numerico(fila.get(c))
                if val and val > 0:
                    altura = val
                    break
            # 2. Intentar cualquier columna que diga "talla" o "altura"
            if altura is None:
                for c in cols_talla:
                    val = normalizar_valor_numerico(fila.get(c))
                    if val and val > 0:
                        altura = val
                        break
        
        if peso is not None and altura is not None:
            break
    
    if not jugador_nombre:
        jugador_nombre = "Jugador sin nombre"
    
    # HEADER DEL PERFIL
    st.subheader("👤 PERFIL DEL JUGADOR")
    
    with st.container():
        col_avatar, col_info = st.columns([1, 3])
        
        with col_avatar:
             mostrar_foto_jugador(jugador_nombre, dni)
             
             st.markdown("<div style='text-align: center; font-size: 0.9rem; margin-top: 0.5rem;'><strong>CLUB UNIVERSITARIO</strong></div>", unsafe_allow_html=True)
             st.markdown("<div style='text-align: center; font-size: 0.9rem;'><strong>DE LA PLATA</strong></div>", unsafe_allow_html=True)
        
        with col_info:
            st.markdown(f"""
            <div style="
                font-size: 3rem;
                font-weight: 900;
                color: #000000;
                margin-bottom: 1rem;
                text-transform: uppercase;
                letter-spacing: 2px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                line-height: 1.1;
                text-align: center;
            ">{jugador_nombre}</div>
            """, unsafe_allow_html=True)
            
            # MÉTRICAS CON ESTILO PERSONALIZADO (SIN EMOJIS)
            info_col1, info_col2, info_col3 = st.columns(3)
            
            with info_col1:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
                    <div style="font-size: 0.85rem; color: #6c757d; font-weight: 600; margin-bottom: 0.5rem;">DNI</div>
                    <div style="font-size: 1.8rem; color: #000000; font-weight: 800;">{dni if dni else "N/A"}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with info_col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
                    <div style="font-size: 0.85rem; color: #6c757d; font-weight: 600; margin-bottom: 0.5rem;">CATEGORÍA</div>
                    <div style="font-size: 1.8rem; color: #000000; font-weight: 800;">{categoria if categoria else "N/A"}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with info_col3:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
                    <div style="font-size: 0.85rem; color: #6c757d; font-weight: 600; margin-bottom: 0.5rem;">POSICIÓN</div>
                    <div style="font-size: 1.8rem; color: #000000; font-weight: 800;">{posicion if posicion else "N/A"}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # SEGUNDA FILA - INFORMACIÓN FÍSICA (SIN EMOJIS)
    col_peso, col_altura, col_estado = st.columns(3)
    
    # PRE-CALCULAR STRINGS DE VISUALIZACIÓN PARA EVITAR ERRORES DE TIPO
    try:
        peso_str = f"{float(peso):.1f} kg" if peso else "N/A"
    except:
        peso_str = str(peso) if peso else "N/A"
        
    try:
        altura_str = f"{float(altura):.1f} cm" if altura else "N/A"
    except:
        altura_str = str(altura) if altura else "N/A"
    
    with col_peso:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
            <div style="font-size: 0.85rem; color: #6c757d; font-weight: 600; margin-bottom: 0.5rem;">PESO</div>
            <div style="font-size: 1.8rem; color: #000000; font-weight: 800;">{peso_str}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_altura:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
            <div style="font-size: 0.85rem; color: #6c757d; font-weight: 600; margin-bottom: 0.5rem;">ALTURA</div>
            <div style="font-size: 1.8rem; color: #000000; font-weight: 800;">{altura_str}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_estado:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
            <div style="font-size: 0.85rem; color: #6c757d; font-weight: 600; margin-bottom: 0.5rem;">ESTADO</div>
            <div style="font-size: 1.8rem; color: #198754; font-weight: 800;">Activo</div>
        </div>
        """, unsafe_allow_html=True)


        
def mostrar_modulo_nutricion(datos_nutricionales):
    """Muestra información del módulo de nutrición"""
    if datos_nutricionales.empty:
        st.info("🥗 No hay datos nutricionales disponibles para este jugador")
        return
    
    st.markdown("### 🥗 Nutrición")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'Peso (kg): [Número con decimales 88,5]' in datos_nutricionales.columns:
            peso_actual = datos_nutricionales['Peso (kg): [Número con decimales 88,5]'].iloc[-1]
            if pd.notna(peso_actual):
                st.metric("⚖️ Peso Actual", f"{peso_actual} kg")
            else:
                st.metric("⚖️ Peso Actual", "N/A")
        else:
            st.metric("⚖️ Peso Actual", "N/A")
    
    with col2:
        if 'IMC' in datos_nutricionales.columns:
            imc = datos_nutricionales['IMC'].iloc[-1]
            if pd.notna(imc):
                st.metric("📊 IMC", f"{imc:.1f}")
            else:
                st.metric("📊 IMC", "N/A")
        else:
            st.metric("📊 IMC", "N/A")
    
    with col3:
        if '% grasa corporal' in datos_nutricionales.columns:
            grasa = datos_nutricionales['% grasa corporal'].iloc[-1]
            if pd.notna(grasa):
                st.metric("🧈 % Grasa", f"{grasa}%")
            else:
                st.metric("🧈 % Grasa", "N/A")
        else:
            st.metric("🧈 % Grasa", "N/A")
    
    # Evolución del peso si hay múltiples registros
    if len(datos_nutricionales) > 1 and 'Peso (kg): [Número con decimales 88,5]' in datos_nutricionales.columns:
        st.subheader("📈 Evolución del Peso")
        pesos = datos_nutricionales['Peso (kg): [Número con decimales 88,5]'].dropna()
        if len(pesos) > 1:
            fig = px.line(x=range(len(pesos)), y=pesos.values, 
                         title="Evolución del Peso Corporal",
                         labels={'x': 'Evaluación', 'y': 'Peso (kg)'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla detallada
    st.subheader("📋 Datos Nutricionales Completos")
    st.dataframe(datos_nutricionales.drop('origen_modulo', axis=1, errors='ignore'), use_container_width=True)

def mostrar_modulo_medico(datos_medicos):
    """Muestra información del módulo médico"""
    if datos_medicos.empty:
        st.info("🏥 No hay datos médicos disponibles para este jugador")
        return
    
    st.markdown('<p class="section-title">🏥 Área Médica</p>', unsafe_allow_html=True)
    
    # Estado actual
    col1, col2 = st.columns(2)
    
    with col1:
        if '¿Puede participar en entrenamientos?' in datos_medicos.columns:
            participacion = datos_medicos['¿Puede participar en entrenamientos?'].iloc[-1]
            if participacion == "Solo entrenamiento diferenciado":
                st.markdown('<div class="status-available">🟡 LIMITADO</div>', unsafe_allow_html=True)
            elif participacion == "No puede entrenar":
                st.markdown('<div class="status-injured">🔴 NO DISPONIBLE</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-available">🟢 DISPONIBLE</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-available">🟢 DISPONIBLE</div>', unsafe_allow_html=True)
    
    with col2:
        total_consultas = len(datos_medicos)
        st.metric("📊 Total Consultas", total_consultas)
    
    # Historial de lesiones
    if 'Tipo de lesión' in datos_medicos.columns:
        st.subheader("🩹 Historial de Lesiones")
        lesiones = datos_medicos['Tipo de lesión'].value_counts()
        if not lesiones.empty:
            fig = px.pie(values=lesiones.values, names=lesiones.index, 
                        title="Distribución por Tipo de Lesión",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
    
    # Severidad de lesiones
    if 'Severidad de la lesión' in datos_medicos.columns:
        st.subheader("⚡ Severidad de Lesiones")
        severidad = datos_medicos['Severidad de la lesión'].value_counts()
        if not severidad.empty:
            fig = px.bar(x=severidad.index, y=severidad.values,
                        title="Distribución por Severidad",
                        color_discrete_sequence=['#e53e3e', '#ed8936', '#38a169'])
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla detallada
    st.subheader("📋 Historial Médico Completo")
    st.dataframe(datos_medicos.drop('origen_modulo', axis=1, errors='ignore'), use_container_width=True)
    
def mostrar_modulo_fisico(datos_fisicos):
    """Muestra información del módulo físico con formato específico Test - Valor - Unidad"""
    if datos_fisicos.empty:
        st.info("💪 No hay datos físicos disponibles para este jugador")
        return
    
    st.markdown("### 💪 Preparación Física")
    
    # Verificar si existen las columnas necesarias
    tiene_test = 'Test' in datos_fisicos.columns
    tiene_subtest = 'Subtest' in datos_fisicos.columns
    tiene_valor = 'valor' in datos_fisicos.columns
    tiene_unidad = 'unidad' in datos_fisicos.columns
    
    if tiene_test and tiene_valor:
        st.subheader("🏋️‍♂️ Resultados de Tests Físicos")
        
        # Crear columnas para mostrar los tests
        tests_unicos = datos_fisicos['Test'].unique()
        
        for test in tests_unicos:
            # Filtrar datos por test
            datos_test = datos_fisicos[datos_fisicos['Test'] == test]
            
            # Si hay subtest, mostrar cada uno
            if tiene_subtest and not datos_test['Subtest'].isna().all():
                for _, fila in datos_test.iterrows():
                    subtest = fila['Subtest'] if pd.notna(fila['Subtest']) else test
                    valor = fila['valor'] if pd.notna(fila['valor']) else 'N/A'
                    unidad = fila['unidad'] if tiene_unidad and pd.notna(fila['unidad']) else ''
                    
                    # Formato específico solicitado
                    if unidad == '"':
                        resultado = f"**{subtest}:** {valor}\""
                    elif unidad == 'kg':
                        resultado = f"**{subtest}:** {valor} kg"
                    else:
                        resultado = f"**{subtest}:** {valor} {unidad}".strip()
                    
                    st.write(f"• {resultado}")
            else:
                # Si no hay subtest, mostrar solo el test principal
                valor = datos_test['valor'].iloc[0] if not datos_test['valor'].isna().any() else 'N/A'
                unidad = datos_test['unidad'].iloc[0] if tiene_unidad and not datos_test['unidad'].isna().any() else ''
                
                if unidad == '"':
                    resultado = f"**{test}:** {valor}\""
                elif unidad == 'kg':
                    resultado = f"**{test}:** {valor} kg"
                else:
                    resultado = f"**{test}:** {valor} {unidad}".strip()
                
                st.write(f"• {resultado}")
        
        # Métricas adicionales
        col1, col2 = st.columns(2)
        
        with col1:
            total_tests = len(tests_unicos)
            st.metric("📊 Tests Realizados", total_tests)
        
        with col2:
            total_evaluaciones = len(datos_fisicos)
            st.metric("📈 Total Evaluaciones", total_evaluaciones)
    
    else:
        # Fallback al método anterior si no están las columnas esperadas
        col1, col2 = st.columns(2)
        
        with col1:
            total_tests = len(datos_fisicos)
            st.metric("📊 Tests Realizados", total_tests)
        
        with col2:
            if 'fecha' in datos_fisicos.columns:
                ultima_fecha = datos_fisicos['fecha'].max()
                st.metric("📅 Último Test", ultima_fecha)
            else:
                st.metric("📅 Último Test", "N/A")
    
    # Tabla detallada completa
    st.subheader("📋 Datos Físicos Completos")
    st.dataframe(datos_fisicos.drop('origen_modulo', axis=1, errors='ignore'), use_container_width=True)


def crear_panel_areas_unificado(datos_jugador):
    """Crea el panel unificado de las 3 áreas con información específica"""
    
    # Separar datos por módulo
    datos_medicos = datos_jugador[datos_jugador['origen_modulo'] == 'medica']
    datos_nutricionales = datos_jugador[datos_jugador['origen_modulo'] == 'nutricion']
    datos_fisicos = datos_jugador[datos_jugador['origen_modulo'] == 'fisica']
    
    st.markdown("### 📊 ÁREAS DE SEGUIMIENTO")
    
    # Crear las 3 columnas principales
    col1, col2, col3 = st.columns(3)
    
    # COLUMNA 1: PREPARACIÓN FÍSICA CON SOMBRA GRIS
    with col1:
        contenido_html = '<div style="padding: 1.5rem; background: #f8f9fa; border-radius: 10px; min-height: 250px; border: 1px solid #dee2e6;">'
        contenido_html += '<h4 style="color: #000000; margin-top: 0;">💪 PREPARACIÓN FÍSICA</h4>'
        
        if datos_fisicos.empty:
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Banco Plano:</strong> —</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Dominadas:</strong> —</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Test Bronco:</strong> —</p>'
        else:
            tiene_test = 'Test' in datos_fisicos.columns
            tiene_subtest = 'Subtest' in datos_fisicos.columns
            tiene_valor = 'valor' in datos_fisicos.columns
            tiene_unidad = 'unidad' in datos_fisicos.columns
            
            if tiene_test and tiene_valor:
                # Mapeo específico según solicitud del usuario
                tests_mapeo = {
                    'Banco Plano': ['banco plano', 'pecho', 'banca'],
                    'Dominadas': ['dominadas', 'pullup', 'pull up'], 
                    'Test Bronco': ['bronco', 'test bronco']
                }
                
                for test_display, keywords in tests_mapeo.items():
                    resultado_encontrado = False
                    
                    # Priorizar búsqueda en SUBTEST como pidió el usuario
                    for _, fila in datos_fisicos.iterrows():
                        test_str = str(fila['Test']).lower() if pd.notna(fila['Test']) else ''
                        subtest_str = str(fila['Subtest']).lower() if tiene_subtest and pd.notna(fila['Subtest']) else ''
                        
                        # Buscar si alguna palabra clave está en Subtest (Prioridad) o Test
                        if any(kw in subtest_str for kw in keywords) or any(kw in test_str for kw in keywords):
                            valor = fila['valor'] if pd.notna(fila['valor']) else 'N/A'
                            unidad = str(fila['unidad']).strip() if tiene_unidad and pd.notna(fila['unidad']) else ''
                            
                            # Formatear unidad
                            if unidad == '"': resultado = f"{valor}\""
                            elif unidad.lower() == 'kg': resultado = f"{valor} kg"
                            elif 'km/h' in unidad.lower(): resultado = f"{valor} km/h"
                            elif unidad.lower() == 's': resultado = f"{valor} s"
                            else: resultado = f"{valor} {unidad}".strip() if unidad else str(valor)
                            
                            contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>{test_display}:</strong> {resultado}</p>'
                            resultado_encontrado = True
                            break
                    
                    if not resultado_encontrado:
                        contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>{test_display}:</strong> —</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Banco Plano:</strong> —</p>'
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Dominadas:</strong> —</p>'
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Test Bronco:</strong> —</p>'
        contenido_html += '</div>'
        st.markdown(contenido_html, unsafe_allow_html=True)
    
    # COLUMNA 2: MEDICINA CON SOMBRA GRIS
    with col2:
        contenido_html = '<div style="padding: 1.5rem; background: #f8f9fa; border-radius: 10px; min-height: 250px; border: 1px solid #dee2e6;">'
        contenido_html += '<h4 style="color: #000000; margin-top: 0;">🏥 MEDICINA</h4>'
        
        if datos_medicos.empty:
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> Sin datos</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Último control:</strong> —</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Lesión activa:</strong> —</p>'
        else:
            if '¿Puede participar en entrenamientos?' in datos_medicos.columns:
                participacion = datos_medicos['¿Puede participar en entrenamientos?'].iloc[-1]
                if participacion == "Solo entrenamiento diferenciado":
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> 🟡 Limitado</p>'
                elif participacion == "No puede entrenar":
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> 🔴 No disponible</p>'
                else:
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> 🟢 Disponible</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Estado actual:</strong> 🟢 Disponible</p>'
            
            if 'Marca temporal' in datos_medicos.columns:
                ultimo_control = datos_medicos['Marca temporal'].max()
                try:
                    fecha_legible = pd.to_datetime(ultimo_control).strftime('%d/%m/%y')
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Último control:</strong> {fecha_legible}</p>'
                except:
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Último control:</strong> {ultimo_control}</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Último control:</strong> —</p>'
            
            if 'Tipo de lesión' in datos_medicos.columns:
                lesion_reciente = datos_medicos['Tipo de lesión'].iloc[-1]
                if pd.notna(lesion_reciente) and lesion_reciente.strip():
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Lesión activa:</strong> {lesion_reciente}</p>'
                else:
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Lesión activa:</strong> Ninguna</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Lesión activa:</strong> —</p>'
        
        contenido_html += '</div>'
        st.markdown(contenido_html, unsafe_allow_html=True)
    
    # COLUMNA 3: NUTRICIÓN CON SOMBRA GRIS
    with col3:
        contenido_html = '<div style="padding: 1.5rem; background: #f8f9fa; border-radius: 10px; min-height: 250px; border: 1px solid #dee2e6;">'
        contenido_html += '<h4 style="color: #000000; margin-top: 0;">🥗 NUTRICIÓN</h4>'
        
        if datos_nutricionales.empty:
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Peso actual:</strong> — kg</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>% grasa corporal:</strong> — %</p>'
            contenido_html += '<p style="margin: 0.5rem 0;">• <strong>IMC:</strong> —</p>'
        else:
            if 'Peso (kg): [Número con decimales 88,5]' in datos_nutricionales.columns:
                peso = datos_nutricionales['Peso (kg): [Número con decimales 88,5]'].iloc[-1]
                if pd.notna(peso):
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Peso actual:</strong> {peso} kg</p>'
                else:
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Peso actual:</strong> — kg</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Peso actual:</strong> — kg</p>'
            
            if '% grasa corporal' in datos_nutricionales.columns:
                grasa = datos_nutricionales['% grasa corporal'].iloc[-1]
                if pd.notna(grasa):
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>% grasa corporal:</strong> {grasa}%</p>'
                else:
                    contenido_html += '<p style="margin: 0.5rem 0;">• <strong>% grasa corporal:</strong> — %</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>% grasa corporal:</strong> — %</p>'
            
            if 'IMC' in datos_nutricionales.columns:
                imc_raw = datos_nutricionales['IMC'].iloc[-1]
                imc = normalizar_valor_numerico(imc_raw)
                if imc is not None:
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>IMC:</strong> {imc:.1f}</p>'
                else:
                    contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>IMC:</strong> {imc_raw if pd.notna(imc_raw) else "—"}</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>IMC:</strong> —</p>'
            
            if 'fecha' in datos_nutricionales.columns:
                ultima_evaluacion = datos_nutricionales['fecha'].max()
                contenido_html += f'<p style="margin: 0.5rem 0;">• <strong>Última evaluación:</strong> {ultima_evaluacion}</p>'
            else:
                contenido_html += '<p style="margin: 0.5rem 0;">• <strong>Última evaluación:</strong> —</p>'
        
        contenido_html += '</div>'
        st.markdown(contenido_html, unsafe_allow_html=True)
        
                
                
# Modificar la función panel_profesional_jugador()
def panel_profesional_jugador():
    """Panel principal profesional para la gestión de jugadores"""
    cargar_estilos_profesionales()
    
    # Header profesional con fondo negro
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #000000 0%, #212529 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        text-align: center;
    ">
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        ">
            <div style="
                width: 80px;
                height: 80px;
                background: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2.5rem;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            ">
                🏉
            </div>
            <div>
                <h1 style="
                    color: white;
                    margin: 0;
                    font-size: 2.5rem;
                    font-weight: 800;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                ">CLUB UNIVERSITARIO DE LA PLATA</h1>
                <p style="
                    color: #ffffff;
                    margin: 0.5rem 0 0 0;
                    font-size: 1.2rem;
                    font-weight: 500;
                    opacity: 0.9;
                ">Panel Profesional de Gestión de Jugadores</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener datos integrados
    with st.spinner("🔄 Cargando datos integrados..."):
        df_combinado = crear_dataframe_integrado()
    
    if df_combinado.empty:
        st.error("❌ No se pudieron cargar datos de los módulos")
        st.info("💡 Verifica las credenciales de Google Sheets y la conexión a internet")
        return
    
    # Selectores superiores
    st.markdown("### 🎯 Selección de Jugador")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Selector de categoría
        categorias_disponibles, col_categoria = obtener_categorias_disponibles(df_combinado)
        categoria_seleccionada = st.selectbox(
            "📋 Seleccionar Categoría:",
            categorias_disponibles,
            key="categoria_selector"
        )
    
    with col2:
        # Selector de jugador
        jugadores_disponibles = obtener_jugadores_por_categoria(
            df_combinado, categoria_seleccionada, col_categoria
        )
        
        if not jugadores_disponibles:
            st.warning("No hay jugadores disponibles en esta categoría")
            return
        
        jugador_seleccionado = st.selectbox(
            "👤 Seleccionar Jugador:",
            jugadores_disponibles,
            key="jugador_selector"
        )
    
    if not jugador_seleccionado:
        st.info("👆 Selecciona un jugador para ver su ficha completa")
        return
    
    # Obtener datos del jugador seleccionado
    datos_jugador = obtener_datos_jugador(df_combinado, jugador_seleccionado)
    
    if datos_jugador.empty:
        st.error("❌ No se encontraron datos para el jugador seleccionado")
        return
    
    st.divider()
    
    # FICHA PERSONAL DEL JUGADOR (ANCHO COMPLETO)
    mostrar_ficha_personal_simple(datos_jugador)
    
    # SEPARADOR
    st.divider()
    
    # ÁREA DE SEGUIMIENTO (ANCHO COMPLETO DEBAJO DE LA FICHA)
    crear_panel_areas_unificado(datos_jugador)
    
    # Footer con información adicional
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        registros_totales = len(datos_jugador)
        st.metric("📊 Registros Totales", registros_totales)
    
    with col2:
        modulos_activos = datos_jugador['origen_modulo'].nunique()
        st.metric("🏢 Módulos con Datos", modulos_activos)
    
    with col3:
        ultima_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.metric("🔄 Última Actualización", ultima_actualizacion)
    
    with col4:
        # Botón de descarga
        csv_datos = datos_jugador.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Datos",
            data=csv_datos,
            file_name=f"universitario_{jugador_seleccionado.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        
def dashboard_360():
    """Función principal del módulo 360"""
    panel_profesional_jugador()