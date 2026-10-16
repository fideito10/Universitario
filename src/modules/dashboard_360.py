import streamlit as st
import pandas as pd
import os
import sys
import re
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.utils.cache import cache_si_ok

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

def _es_jugador():
    """True si la sesion actual tiene rol Jugador (solo presentacion)."""
    try:
        from src.security.auth import get_auth_manager
        return bool(get_auth_manager().is_role("Jugador"))
    except Exception:
        return False


def aviso_jugador(icono, titulo, texto):
    """Tarjeta oscura amable para mensajes que ve un jugador."""
    st.markdown(
        '<div class="u360-card" style="--acc:#ffffff;text-align:center;padding:1.4rem 1.1rem">'
        f'<div style="font-size:2.2rem;line-height:1">{icono}</div>'
        f'<div class="u360-card-t" style="justify-content:center;margin:.6rem 0 .3rem 0;color:#fff">{_esc(titulo)}</div>'
        f'<div class="u360-empty">{_esc(texto)}</div></div>',
        unsafe_allow_html=True)


@cache_si_ok(ttl=300)
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

@cache_si_ok(ttl=300)
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

@cache_si_ok(ttl=300)
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

@cache_si_ok(ttl=300)
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

@cache_si_ok(ttl=300)
def crear_dataframe_integrado():
    """Combina los datos usando la Base Central de Universitario como fuente de verdad"""
    df_central = obtener_df_central()
    if df_central.empty:
        if _es_jugador():
            st.session_state['_u360_aviso_mostrado'] = True
            aviso_jugador("📋", "Todavía no tenemos tus datos", "Todavía no tenemos tus datos cargados. Consultá con el cuerpo técnico.")
        else:
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

    def limpiar_df_para_concat(df):
        """Elimina columnas duplicadas y normaliza nombres con sufijos del merge."""
        # 1. Quitar sufijos _test / _central generados por pd.merge en areafisica
        nuevos_nombres = {}
        for col in df.columns:
            if col.endswith('_test') or col.endswith('_central'):
                base = col.rsplit('_', 1)[0]
                # Solo renombrar si la versión base no existe ya
                if base not in df.columns:
                    nuevos_nombres[col] = base
                else:
                    nuevos_nombres[col] = None  # marcar para eliminar
        # Eliminar columnas marcadas para quitar
        cols_eliminar = [c for c, v in nuevos_nombres.items() if v is None]
        df = df.drop(columns=cols_eliminar, errors='ignore')
        # Renombrar las que quedaron
        df = df.rename(columns={k: v for k, v in nuevos_nombres.items() if v is not None})

        # 2. Eliminar columnas con nombre duplicado (quedarse con la primera aparición)
        df = df.loc[:, ~df.columns.duplicated()]

        return df.reset_index(drop=True)

    # Limpiar y resetear índices antes de concatenar para evitar InvalidIndexError
    registros_finales = [limpiar_df_para_concat(df) for df in registros_finales if not df.empty]

    if not registros_finales:
        return pd.DataFrame()

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
        os.path.join(os.getcwd(), 'assets', 'fotos_jugadores'),
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
            max-width: 60vw;
            aspect-ratio: 1 / 1; 
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Montserrat:wght@700;800;900&family=Outfit:wght@500;600;700;800&display=swap');
    
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
        /* --- Ajustes mobile (360-430px) --- */
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 0.6rem !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto;
            gap: 4px;
            flex-wrap: nowrap;
        }
        .stTabs [data-baseweb="tab"] {
            height: 44px;
            min-width: max-content;
            padding: 0 0.8rem;
            font-size: 0.85rem;
        }
        .stButton > button, .stDownloadButton > button {
            min-height: 44px;
            width: 100%;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.5rem;
            overflow-wrap: anywhere;
        }
        div[data-testid="stDataFrame"] {
            overflow-x: auto;
        }
        .module-tab { padding: 0.6rem; }
        .player-card { padding: 1rem; border-left-width: 6px; }
    }

    /* ===== Panel 360 - tarjetas dark mobile-first ===== */
    .u360-hdr { background: linear-gradient(135deg,#000 0%,#212529 100%); border-radius: 16px; padding: 1rem 1.2rem; margin-bottom: 1rem; display:flex; align-items:center; gap:.9rem; box-shadow: 0 8px 24px rgba(0,0,0,.25); }
    .u360-hdr-ico { width:48px; height:48px; flex:none; background:#fff; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.5rem; }
    .u360-hdr-t { color:#fff; margin:0; font-family:'Montserrat',sans-serif; font-weight:800; text-transform:uppercase; font-size:clamp(.95rem,4.2vw,1.6rem); line-height:1.15; letter-spacing:.5px; }
    .u360-hdr-s { color:#bbb; margin:.2rem 0 0 0; font-size:clamp(.72rem,3vw,.95rem); text-transform:uppercase; letter-spacing:1px; }
    .u360-hero { background: linear-gradient(135deg,#000 0%,#2d2d2d 100%); border-radius:16px; padding:1rem; display:flex; align-items:center; gap:1rem; color:#fff; box-shadow:0 6px 20px rgba(0,0,0,.25); }
    .u360-photo { width:92px; height:92px; flex:none; border-radius:14px; border:2px solid #fff; object-fit:cover; background:#1c1c1c; }
    .u360-photo-ph { display:flex; align-items:center; justify-content:center; font-size:2.6rem; }
    .u360-hero-info { min-width:0; flex:1; }
    .u360-kicker { font-size:.7rem; letter-spacing:2px; text-transform:uppercase; color:#aaa; font-weight:600; }
    .u360-name { font-family:'Montserrat',sans-serif; font-weight:900; text-transform:uppercase; font-size:clamp(1.05rem,5.2vw,1.9rem); line-height:1.1; word-break:break-word; margin:.15rem 0 .5rem 0; color:#fff; }
    .u360-chips { display:flex; flex-wrap:wrap; gap:.35rem; }
    .u360-chip { background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.2); border-radius:999px; padding:.2rem .65rem; font-size:.74rem; color:#fff; white-space:nowrap; }
    .u360-chip b { color:#aaa; font-weight:600; margin-right:.2rem; }
    .u360-stats { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.5rem; margin:.6rem 0 1.2rem 0; }
    .u360-stat { background:linear-gradient(135deg,#111 0%,#2d2d2d 100%); border-radius:12px; padding:.8rem .4rem; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,.2); }
    .u360-stat-l { font-size:.68rem; letter-spacing:1.5px; text-transform:uppercase; color:#aaa; font-weight:600; margin-bottom:.35rem; }
    .u360-stat-v { font-family:'Montserrat',sans-serif; font-weight:900; font-size:clamp(1rem,4.6vw,1.6rem); color:#fff; line-height:1.1; white-space:nowrap; }
    .u360-h { font-family:'Montserrat',sans-serif; font-weight:800; text-transform:uppercase; letter-spacing:1px; font-size:1.05rem; color:#000; margin:.4rem 0 .2rem 0; }
    .u360-sub { font-family:'Montserrat',sans-serif; font-weight:700; text-transform:uppercase; letter-spacing:1px; font-size:.8rem; color:#6c757d; margin:1rem 0 .3rem 0; }
    .u360-card { background:linear-gradient(135deg,#0d0d0d 0%,#2a2a2a 100%); border-radius:16px; border-left:6px solid var(--acc,#fff); padding:1rem 1.1rem; margin-top:.4rem; color:#fff; box-shadow:0 6px 18px rgba(0,0,0,.22); }
    .u360-card-t { display:flex; align-items:center; gap:.6rem; font-family:'Montserrat',sans-serif; font-weight:800; text-transform:uppercase; letter-spacing:1px; font-size:.95rem; color:var(--acc,#fff); margin-bottom:.4rem; }
    .u360-ico { font-size:1.4rem; }
    .u360-row { display:flex; justify-content:space-between; align-items:center; gap:.8rem; padding:.75rem 0; border-bottom:1px solid rgba(255,255,255,.1); min-height:44px; }
    .u360-row:last-child { border-bottom:none; }
    .u360-row-l { color:#b5b5b5; font-size:.88rem; }
    .u360-row-v { color:#fff; font-weight:700; font-size:1rem; text-align:right; word-break:break-word; }
    .u360-empty { color:#cfcfcf; font-size:.92rem; line-height:1.45; padding:.4rem 0 .2rem 0; }
    .u360-foot { color:#6c757d; font-size:.75rem; text-align:center; margin:1.2rem 0 .4rem 0; }
    .stTabs [role="tablist"] { gap:6px; border-bottom:none !important; }
    .stTabs [data-testid="stTab"] { flex:1 1 0; justify-content:center; min-height:46px; height:46px; border-radius:12px; background:#f1f3f5; border:1px solid #dee2e6; }
    .stTabs [data-testid="stTab"] p { margin:0; font-weight:700; color:#000; white-space:nowrap; }
    .stTabs [data-testid="stTab"][aria-selected="true"] { background:linear-gradient(135deg,#000 0%,#2d2d2d 100%); border-color:#000; }
    .stTabs [data-testid="stTab"][aria-selected="true"] p { color:#fff; }
    .stTabs .react-aria-SelectionIndicator, .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none !important; }
    @media (max-width: 768px) {
        .u360-hero { padding:.85rem; gap:.8rem; }
        .u360-photo { width:78px; height:78px; }
        .stTabs [data-testid="stTab"] { padding: 0 .3rem; }
        .stTabs [data-testid="stTab"] p { font-size:.85rem; }
    }
    </style>
    """, unsafe_allow_html=True)


def aplicar_layout_movil(fig, height=320):
    """Ajusta un grafico plotly para pantallas chicas (no altera datos)."""
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        title=dict(font=dict(size=14)),
    )
    return fig


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



# ---------------------------------------------------------------------------
# PRESENTACION (mobile-first): ficha + areas de seguimiento
# ---------------------------------------------------------------------------
import html as _html
import base64 as _b64

ACENTO_FISICA = "#ff9800"
ACENTO_MEDICA = "#ef5350"
ACENTO_NUTRI = "#66bb6a"


def _esc(valor):
    return _html.escape(str(valor)) if valor is not None else ""


def _buscar_foto_path(nombre_jugador, dni_jugador):
    """Devuelve la ruta de la foto del jugador (por DNI o nombre) o None."""
    dni_limpio = str(dni_jugador).strip().replace('.', '') if dni_jugador else None
    nombre_limpio = str(nombre_jugador).strip() if nombre_jugador else None
    for base_dir in [os.path.join(os.getcwd(), 'src', 'assets', 'fotos_jugadores'),
                     os.path.join(os.getcwd(), 'assets', 'fotos_jugadores')]:
        if not os.path.exists(base_dir):
            continue
        for ident in (dni_limpio, nombre_limpio):
            if not ident:
                continue
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                p = os.path.join(base_dir, f"{ident}{ext}")
                if os.path.exists(p):
                    return p
    return None


@cache_si_ok(ttl=3600)
def _foto_data_uri_path(p):
    try:
        ext = os.path.splitext(p)[1].lower().lstrip('.')
        mime = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'webp': 'webp'}.get(ext, 'jpeg')
        with open(p, 'rb') as f:
            return f"data:image/{mime};base64," + _b64.b64encode(f.read()).decode()
    except Exception:
        return None


def _foto_data_uri(nombre_jugador, dni_jugador):
    p = _buscar_foto_path(nombre_jugador, dni_jugador)
    if not p:
        return None
    return _foto_data_uri_path(p)


def _fila_dato(etiqueta, valor, color_valor=None):
    estilo = f' style="color:{color_valor}"' if color_valor else ''
    return (f'<div class="u360-row"><span class="u360-row-l">{_esc(etiqueta)}</span>'
            f'<span class="u360-row-v"{estilo}>{valor}</span></div>')


def _tarjeta_area(icono, titulo, acento, filas_html, vacio_msg=None):
    cuerpo = filas_html if not vacio_msg else f'<div class="u360-empty">{_esc(vacio_msg)}</div>'
    return (f'<div class="u360-card" style="--acc:{acento}">'
            f'<div class="u360-card-t"><span class="u360-ico">{icono}</span>{_esc(titulo)}</div>'
            f'{cuerpo}</div>')


def mostrar_ficha_personal_simple(datos_jugador):
    """Ficha personal del jugador: tarjeta hero + 3 indicadores (mobile-first)."""
    if datos_jugador.empty:
        st.warning("No se encontraron datos del jugador")
        return

    jugador_nombre = None
    dni = None
    categoria = None
    posicion = None
    peso = None
    altura = None

    for _, fila in datos_jugador.iterrows():
        if pd.notna(fila.get('Nombre completo del jugador')):
            jugador_nombre = fila['Nombre completo del jugador']
        elif pd.notna(fila.get('Nombre y Apellido')):
            jugador_nombre = fila['Nombre y Apellido']
        elif pd.notna(fila.get('Nombre')) and pd.notna(fila.get('Apellido')):
            jugador_nombre = f"{fila['Nombre']} {fila['Apellido']}"

        if pd.notna(fila.get('DNI')):
            dni = fila['DNI']
        elif pd.notna(fila.get('Dni')):
            dni = fila['Dni']
        elif pd.notna(fila.get('Por Favor completa el Dni')):
            dni = fila['Por Favor completa el Dni']

        if pd.notna(fila.get('Categoria')):
            categoria = fila['Categoria']
        elif pd.notna(fila.get('Categoría')):
            categoria = fila['Categoría']

        if pd.notna(fila.get('Posicion')):
            posicion = fila['Posicion']
        elif pd.notna(fila.get('Posición del jugador')):
            posicion = fila['Posición del jugador']
        elif pd.notna(fila.get('Posición')):
            posicion = fila['Posición']

    cols_peso = [c for c in datos_jugador.columns if 'peso' in str(c).lower()]
    cols_talla = [c for c in datos_jugador.columns if any(p in str(c).lower() for p in ['talla', 'altura', 'estatura'])]
    datos_buscar = datos_jugador.sort_index(ascending=False)

    for _, fila in datos_buscar.iterrows():
        if peso is None:
            for c in ['Peso (kg): [Número con decimales 88,5]', 'Peso']:
                val = normalizar_valor_numerico(fila.get(c))
                if val and val > 0:
                    peso = val
                    break
            if peso is None:
                for c in cols_peso:
                    val = normalizar_valor_numerico(fila.get(c))
                    if val and val > 0:
                        peso = val
                        break
        if altura is None:
            for c in ['Talla (cm): [Número]', 'Talla', 'Altura']:
                val = normalizar_valor_numerico(fila.get(c))
                if val and val > 0:
                    altura = val
                    break
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

    try:
        peso_str = f"{float(peso):.1f} kg" if peso else "—"
    except Exception:
        peso_str = str(peso) if peso else "—"
    try:
        altura_str = f"{float(altura):.0f} cm" if altura else "—"
    except Exception:
        altura_str = str(altura) if altura else "—"

    foto = _foto_data_uri(jugador_nombre, dni)
    if foto:
        foto_html = f'<img class="u360-photo" src="{foto}" alt="Foto del jugador">'
    else:
        foto_html = '<div class="u360-photo u360-photo-ph">👤</div>'

    chips = ""
    if dni:
        chips += f'<span class="u360-chip"><b>DNI</b> {_esc(dni)}</span>'
    if categoria:
        chips += f'<span class="u360-chip"><b>CAT.</b> {_esc(categoria)}</span>'
    if posicion:
        chips += f'<span class="u360-chip"><b>POS.</b> {_esc(posicion)}</span>'
    if not chips:
        chips = '<span class="u360-chip">Datos personales sin completar</span>'

    st.markdown(f"""
    <div class="u360-hero">
        {foto_html}
        <div class="u360-hero-info">
            <div class="u360-kicker">Mi ficha</div>
            <div class="u360-name">{_esc(jugador_nombre)}</div>
            <div class="u360-chips">{chips}</div>
        </div>
    </div>
    <div class="u360-stats">
        <div class="u360-stat"><div class="u360-stat-l">Peso</div><div class="u360-stat-v">{_esc(peso_str)}</div></div>
        <div class="u360-stat"><div class="u360-stat-l">Altura</div><div class="u360-stat-v">{_esc(altura_str)}</div></div>
        <div class="u360-stat"><div class="u360-stat-l">Estado</div><div class="u360-stat-v" style="color:#66bb6a">Activo</div></div>
    </div>
    """, unsafe_allow_html=True)


def _html_area_fisica(datos_fisicos):
    if datos_fisicos.empty:
        return _tarjeta_area("💪", "Preparación física", ACENTO_FISICA, "",
                             "Todavía no hay tests físicos cargados. Cuando el preparador los registre, vas a verlos acá.")
    tiene_test = 'Test' in datos_fisicos.columns
    tiene_subtest = 'Subtest' in datos_fisicos.columns
    tiene_valor = 'valor' in datos_fisicos.columns
    tiene_unidad = 'unidad' in datos_fisicos.columns

    if not (tiene_test and tiene_valor):
        return _tarjeta_area("💪", "Preparación física", ACENTO_FISICA, "",
                             "Todavía no hay resultados de tests para mostrar.")

    def fmt(valor, unidad):
        unidad = str(unidad).strip() if unidad is not None and pd.notna(unidad) else ''
        if unidad == '"':
            return f'{valor}"'
        return f"{valor} {unidad}".strip() if unidad else str(valor)

    tests_mapeo = {
        'Banco Plano': ['banco plano', 'pecho', 'banca'],
        'Dominadas': ['dominadas', 'pullup', 'pull up'],
        'Test Bronco': ['bronco', 'test bronco'],
    }
    filas = ""
    for test_display, keywords in tests_mapeo.items():
        resultado = "—"
        for _, fila in datos_fisicos.iterrows():
            test_str = str(fila['Test']).lower() if pd.notna(fila['Test']) else ''
            subtest_str = str(fila['Subtest']).lower() if tiene_subtest and pd.notna(fila['Subtest']) else ''
            if any(kw in subtest_str for kw in keywords) or any(kw in test_str for kw in keywords):
                valor = fila['valor'] if pd.notna(fila['valor']) else 'N/A'
                resultado = fmt(valor, fila['unidad'] if tiene_unidad else '')
                break
        filas += _fila_dato(test_display, _esc(resultado))
    return _tarjeta_area("💪", "Preparación física", ACENTO_FISICA, filas)


def _html_area_medica(datos_medicos):
    if datos_medicos.empty:
        return _tarjeta_area("🏥", "Área médica", ACENTO_MEDICA, "",
                             "No tenés registros médicos cargados. ¡Buena señal!")
    filas = ""
    estado, color = "🟢 Disponible", "#66bb6a"
    if '¿Puede participar en entrenamientos?' in datos_medicos.columns:
        participacion = datos_medicos['¿Puede participar en entrenamientos?'].iloc[-1]
        if participacion == "Solo entrenamiento diferenciado":
            estado, color = "🟡 Limitado", "#ffca28"
        elif participacion == "No puede entrenar":
            estado, color = "🔴 No disponible", "#ef5350"
    filas += _fila_dato("Estado actual", estado, color)

    if 'Marca temporal' in datos_medicos.columns:
        ultimo_control = datos_medicos['Marca temporal'].max()
        try:
            fecha = pd.to_datetime(ultimo_control).strftime('%d/%m/%y')
        except Exception:
            fecha = _esc(ultimo_control)
        filas += _fila_dato("Último control", fecha)
    else:
        filas += _fila_dato("Último control", "—")

    if 'Tipo de lesión' in datos_medicos.columns:
        lesion = datos_medicos['Tipo de lesión'].iloc[-1]
        if pd.notna(lesion) and str(lesion).strip():
            filas += _fila_dato("Lesión activa", _esc(lesion))
        else:
            filas += _fila_dato("Lesión activa", "Ninguna")
    else:
        filas += _fila_dato("Lesión activa", "—")
    return _tarjeta_area("🏥", "Área médica", ACENTO_MEDICA, filas)


def _preparar_nutricion(datos_nutricionales):
    df_nut_ord = datos_nutricionales.copy()
    col_fecha = next((c for c in df_nut_ord.columns if any(p in str(c).lower() for p in ['marca', 'fecha'])), None)
    if col_fecha:
        df_nut_ord[col_fecha] = pd.to_datetime(df_nut_ord[col_fecha], errors='coerce')
        ordenado = df_nut_ord.dropna(subset=[col_fecha]).sort_values(col_fecha)
        if not ordenado.empty:
            df_nut_ord = ordenado
    return df_nut_ord, col_fecha


def _col_peso_nutri(df):
    col = 'Peso (kg): [Número con decimales 88,5]'
    if col not in df.columns:
        col = next((c for c in df.columns if 'peso' in str(c).lower() and 'kg' in str(c).lower()), None)
    return col


def _html_area_nutricion(datos_nutricionales):
    msg_vacio = "Todavía no hay controles nutricionales cargados. Cuando el nutricionista te evalúe, vas a verlos acá."
    if datos_nutricionales.empty:
        return _tarjeta_area("🥗", "Nutrición", ACENTO_NUTRI, "", msg_vacio)
    df_nut_ord, col_fecha = _preparar_nutricion(datos_nutricionales)
    if df_nut_ord.empty:
        return _tarjeta_area("🥗", "Nutrición", ACENTO_NUTRI, "", msg_vacio)

    ultimo = df_nut_ord.iloc[-1]
    col_peso = _col_peso_nutri(df_nut_ord)
    peso_val = normalizar_valor_numerico(ultimo.get(col_peso)) if col_peso else None

    col_grasa = '% MA: [Número con decimales]'
    if col_grasa not in df_nut_ord.columns:
        col_grasa = next((c for c in df_nut_ord.columns if '%' in str(c).lower() and ('ma' in str(c).lower() or 'adip' in str(c).lower())), None)
    grasa_val = normalizar_valor_numerico(ultimo.get(col_grasa)) if col_grasa else None

    col_imc = 'IMC'
    if col_imc not in df_nut_ord.columns:
        col_imc = next((c for c in df_nut_ord.columns if 'imc' in str(c).lower()), None)
    imc_val = normalizar_valor_numerico(ultimo.get(col_imc)) if col_imc else None

    fecha_val = ultimo.get(col_fecha) if col_fecha else None
    try:
        fecha_dt = pd.to_datetime(fecha_val)
        meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        fecha_str = meses_es.get(fecha_dt.month, "—") if pd.notna(fecha_dt) else "—"
    except Exception:
        fecha_str = str(fecha_val) if pd.notna(fecha_val) else "—"

    filas = (_fila_dato("Peso actual", f"{peso_val:.1f} kg" if peso_val else "—")
             + _fila_dato("% grasa corporal", f"{grasa_val:.1f} %" if grasa_val else "—")
             + _fila_dato("IMC", f"{imc_val:.1f}" if imc_val else "—")
             + _fila_dato("Última evaluación", _esc(fecha_str)))
    return _tarjeta_area("🥗", "Nutrición", ACENTO_NUTRI, filas)


def _grafico_peso(datos_nutricionales):
    """Evolucion del peso (solo si hay 2+ controles). No altera datos."""
    if datos_nutricionales.empty:
        return
    df, col_fecha = _preparar_nutricion(datos_nutricionales)
    col_peso = _col_peso_nutri(df)
    if not col_peso:
        return
    serie = df.assign(_p=df[col_peso].apply(normalizar_valor_numerico))
    serie = serie.dropna(subset=['_p'])
    if len(serie) < 2:
        return
    usa_fecha = bool(col_fecha) and serie[col_fecha].notna().all()
    x = serie[col_fecha] if usa_fecha else list(range(1, len(serie) + 1))
    fig = go.Figure(go.Scatter(x=x, y=serie['_p'], mode='lines+markers',
                               line=dict(color=ACENTO_NUTRI, width=3),
                               marker=dict(size=8, color='#ffffff', line=dict(color=ACENTO_NUTRI, width=2))))
    fig.update_layout(
        height=240, margin=dict(l=8, r=8, t=10, b=8), showlegend=False,
        paper_bgcolor='#111111', plot_bgcolor='#111111', font=dict(color='#e5e5e5', size=12),
        xaxis=dict(showgrid=False, tickformat='%b %y' if usa_fecha else None, nticks=4, fixedrange=True),
        yaxis=dict(gridcolor='#2a2a2a', ticksuffix=' kg', fixedrange=True),
    )
    st.markdown('<div class="u360-sub">Evolución del peso</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def crear_panel_areas_unificado(datos_jugador):
    """Areas de seguimiento en pestañas (Fisica / Medica / Nutricion)."""
    datos_medicos = datos_jugador[datos_jugador['origen_modulo'] == 'medica']
    datos_nutricionales = datos_jugador[datos_jugador['origen_modulo'] == 'nutricion']
    datos_fisicos = datos_jugador[datos_jugador['origen_modulo'] == 'fisica']

    st.markdown('<div class="u360-h">Áreas de seguimiento</div>', unsafe_allow_html=True)
    tab_f, tab_m, tab_n = st.tabs(["💪 Física", "🏥 Médica", "🥗 Nutrición"])
    with tab_f:
        st.markdown(_html_area_fisica(datos_fisicos), unsafe_allow_html=True)
    with tab_m:
        st.markdown(_html_area_medica(datos_medicos), unsafe_allow_html=True)
    with tab_n:
        st.markdown(_html_area_nutricion(datos_nutricionales), unsafe_allow_html=True)
        _grafico_peso(datos_nutricionales)


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
            aplicar_layout_movil(fig)
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
            aplicar_layout_movil(fig)
            st.plotly_chart(fig, use_container_width=True)
    
    # Severidad de lesiones
    if 'Severidad de la lesión' in datos_medicos.columns:
        st.subheader("⚡ Severidad de Lesiones")
        severidad = datos_medicos['Severidad de la lesión'].value_counts()
        if not severidad.empty:
            fig = px.bar(x=severidad.index, y=severidad.values,
                        title="Distribución por Severidad",
                        color_discrete_sequence=['#e53e3e', '#ed8936', '#38a169'])
            aplicar_layout_movil(fig)
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


# Modificar la función panel_profesional_jugador()
def panel_profesional_jugador():
    """Panel principal profesional para la gestión de jugadores"""
    cargar_estilos_profesionales()
    
    # Header compacto (negro)
    st.markdown("""
    <div class="u360-hdr">
        <div class="u360-hdr-ico">🏉</div>
        <div>
            <div class="u360-hdr-t">Club Universitario de La Plata</div>
            <div class="u360-hdr-s">Panel 360° del jugador</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Obtener datos integrados
    with st.spinner("🔄 Cargando datos integrados..."):
        st.session_state['_u360_aviso_mostrado'] = False
        df_combinado = crear_dataframe_integrado()
    
    if df_combinado.empty:
        if _es_jugador():
            # (si la Base Central estaba vacia, el aviso ya se mostro arriba)
            if not st.session_state.get('_u360_aviso_mostrado'):
                aviso_jugador("📡", "No pudimos cargar tu panel", "Intentá de nuevo en unos minutos. Si sigue igual, consultá con el cuerpo técnico.")
        else:
            st.error("❌ No se pudieron cargar datos de los módulos")
            st.info("💡 Verifica las credenciales de Google Sheets y la conexión a internet")
        return
    
    # Identificar si es un jugador (Filtro automático por DNI)
    from src.security.auth import get_auth_manager
    am = get_auth_manager()
    
    user_dni = st.session_state.user.get('dni', '')
    is_player = am.is_role("Jugador")
    jugador_seleccionado = None
    
    if is_player and user_dni:
        # Buscar el nombre del jugador que coincide con el DNI en el dataframe
        col_dni = buscar_columna_dni(df_combinado)
        if col_dni:
            # Asegurar que comparamos strings limpios y normalizados (sin puntos ni decimales)
            df_combinado[col_dni] = df_combinado[col_dni].apply(normalizar_dni)
            dni_busqueda = normalizar_dni(user_dni)
            
            player_row = df_combinado[df_combinado[col_dni] == dni_busqueda]
            if not player_row.empty:
                col_nombre = buscar_columna_jugador(df_combinado) or df_combinado.columns[0]
                jugador_seleccionado = player_row.iloc[0][col_nombre]
                # obtener_datos_jugador espera el formato 'Nombre (DNI: 123)'
                jugador_seleccionado = f"{jugador_seleccionado} (DNI: {dni_busqueda})"
            else:
                aviso_jugador("🔎", "No encontramos tus registros", "Todavía no tenemos tus datos cargados. Consultá con el cuerpo técnico.")
                return
        else:
            aviso_jugador("📡", "No pudimos cargar tu panel", "Intentá de nuevo en unos minutos. Si sigue igual, consultá con el cuerpo técnico.")
            return
    else:
        # Selectores superiores para otros roles
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
        if is_player and user_dni:
            aviso_jugador("🔎", "No encontramos tus registros", "Todavía no tenemos tus datos cargados. Consultá con el cuerpo técnico.")
        else:
            st.error("❌ No se encontraron datos para el jugador seleccionado")
        return
    
    if not (is_player and user_dni):
        st.divider()

    # FICHA PERSONAL DEL JUGADOR (ANCHO COMPLETO)
    mostrar_ficha_personal_simple(datos_jugador)

    # ÁREA DE SEGUIMIENTO (ANCHO COMPLETO DEBAJO DE LA FICHA)
    crear_panel_areas_unificado(datos_jugador)

    # El jugador solo ve su propia ficha: sin metricas ni descargas de staff
    if is_player and user_dni:
        st.markdown(f'<div class="u360-foot">Actualizado: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)
        return

    # Footer con información adicional (staff)
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