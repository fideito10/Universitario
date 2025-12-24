import streamlit as st
import pandas as pd
import gspread
import time
from datetime import datetime, date
from src.modules.administracion import JugadoresMaestroManager

class AsistenciaManager:
    def __init__(self):
        self.admin_manager = JugadoresMaestroManager()
        self.sheet_id = "1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw"
        self.worksheet_name = "Asistencias"
        
        # **NUEVO: Cache para evitar consultas repetidas**
        if 'sheets_cache' not in st.session_state:
            st.session_state.sheets_cache = {}
        if 'last_request_time' not in st.session_state:
            st.session_state.last_request_time = 0
    
    def rate_limit_check(self):
        """Verificar rate limit - esperar si es necesario"""
        current_time = time.time()
        time_since_last = current_time - st.session_state.last_request_time
        
        # Esperar mínimo 1 segundo entre requests
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        
        st.session_state.last_request_time = time.time()
    
    def get_or_create_attendance_sheet(self):
        """Obtener o crear hoja de asistencias CON CACHE"""
        cache_key = f"attendance_sheet_{self.worksheet_name}"
        
        # Verificar cache (válido por 5 minutos)
        if cache_key in st.session_state.sheets_cache:
            cache_data = st.session_state.sheets_cache[cache_key]
            if (time.time() - cache_data['timestamp']) < 300:  # 5 minutos
                return cache_data['sheet']
        
        try:
            # Rate limiting
            self.rate_limit_check()
            
            worksheet = self.admin_manager.connect_to_sheet()
            if not worksheet:
                return None
            
            spreadsheet = worksheet.spreadsheet
            
            # Intentar abrir hoja de asistencias
            try:
                # Rate limiting para segunda consulta
                self.rate_limit_check()
                attendance_sheet = spreadsheet.worksheet(self.worksheet_name)
                
                # Guardar en cache
                st.session_state.sheets_cache[cache_key] = {
                    'sheet': attendance_sheet,
                    'timestamp': time.time()
                }
                
                return attendance_sheet
                
            except:
                # Crear nueva hoja si no existe
                st.info("📋 Creando hoja de asistencias...")
                
                # Rate limiting para crear hoja
                self.rate_limit_check()
                attendance_sheet = spreadsheet.add_worksheet(
                    title=self.worksheet_name, 
                    rows=1000, 
                    cols=8
                )
                
                # Headers para asistencias
                headers = [
                    "Fecha", "Categoria", "Tipo_Actividad", "DNI", 
                    "Nombre", "Apellido", "Estado_Asistencia", "Observaciones"
                ]
                
                # Rate limiting para agregar headers
                self.rate_limit_check()
                attendance_sheet.append_row(headers)
                
                # Guardar en cache
                st.session_state.sheets_cache[cache_key] = {
                    'sheet': attendance_sheet,
                    'timestamp': time.time()
                }
                
                st.success("✅ Hoja de asistencias creada")
                return attendance_sheet
                
        except Exception as e:
            st.error(f"❌ Error con hoja de asistencias: {e}")
            return None
    
    def save_attendance(self, attendance_data, fecha, categoria, tipo_actividad):
        """Guardar asistencia en Google Sheets CON RATE LIMITING"""
        sheet = self.get_or_create_attendance_sheet()
        if not sheet:
            return False
        
        try:
            # Preparar TODOS los datos en una sola operación
            rows_to_insert = []
            for player in attendance_data:
                row_data = [
                    fecha.strftime('%d/%m/%Y'),
                    categoria,
                    tipo_actividad,
                    str(player['dni']),
                    player['nombre'],
                    player['apellido'],
                    player['estado_asistencia'],  # Nuevo: Presente/Ausente/Lesionado
                    player.get('observaciones', '')  # Observaciones opcionales
                ]
                rows_to_insert.append(row_data)
            
            # **IMPORTANTE: Una sola operación batch en lugar de múltiples append_row**
            if rows_to_insert:
                # Rate limiting antes de operación batch
                self.rate_limit_check()
                
                # Obtener siguiente fila vacía
                all_values = sheet.get_all_values()
                next_row = len(all_values) + 1
                
                # Insertar todos los datos de una vez
                range_name = f"A{next_row}:H{next_row + len(rows_to_insert) - 1}"
                sheet.update(range_name, rows_to_insert)
                
                st.success(f"✅ {len(rows_to_insert)} registros guardados exitosamente")
            
            return True
            
        except Exception as e:
            if "RATE_LIMIT_EXCEEDED" in str(e) or "429" in str(e):
                st.error("⏳ Límite de consultas excedido. Espere un momento e intente nuevamente.")
                st.info("💡 Consejo: Evite hacer múltiples operaciones muy rápido")
            else:
                st.error(f"❌ Error guardando asistencia: {e}")
            return False
    
    def get_attendance_report(self, fecha_desde=None, fecha_hasta=None):
        """Obtener reporte de asistencias CON CACHE"""
        cache_key = f"attendance_report_{fecha_desde}_{fecha_hasta}"
        
        # Verificar cache (válido por 2 minutos para reportes)
        if cache_key in st.session_state.sheets_cache:
            cache_data = st.session_state.sheets_cache[cache_key]
            if (time.time() - cache_data['timestamp']) < 120:  # 2 minutos
                return cache_data['data']
        
        sheet = self.get_or_create_attendance_sheet()
        if not sheet:
            return pd.DataFrame()
        
        try:
            # Rate limiting
            self.rate_limit_check()
            
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            
            if not df.empty and fecha_desde and fecha_hasta:
                # Filtrar por fechas si se especifican
                df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')
                df = df[(df['Fecha'] >= fecha_desde) & (df['Fecha'] <= fecha_hasta)]
            
            # Guardar en cache
            st.session_state.sheets_cache[cache_key] = {
                'data': df,
                'timestamp': time.time()
            }
            
            return df
            
        except Exception as e:
            if "RATE_LIMIT_EXCEEDED" in str(e) or "429" in str(e):
                st.error("⏳ Límite de consultas excedido. Intente nuevamente en un minuto.")
            else:
                st.error(f"❌ Error obteniendo reporte: {e}")
            return pd.DataFrame()

def main_lista():
    """Función principal del módulo Lista - INTERFAZ LIMPIA"""
    
    # **CSS OPTIMIZADO PARA LISTA DE ASISTENCIA**
    st.markdown("""
    <style>
    /* Container principal limpio */
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* Header principal de Lista */
    .lista-main-header {
        text-align: center;
        background: linear-gradient(135deg, #000000 0%, #2C2C2C 50%, #1A1A1A 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 25px;
        padding: 20px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .lista-main-header h1 {
        font-size: 2.2rem;
        margin-bottom: 8px;
        font-weight: bold;
    }
    
    .lista-main-header h2 {
        font-size: 1.2rem;
        margin: 0;
        opacity: 0.9;
        font-weight: normal;
    }
    
    /* Botones optimizados para touch */
    .stButton > button {
        height: 55px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1) !important;
    }
    
    /* Cards de jugadores mejoradas */
    .player-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 3px 6px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .player-card.presente {
        border-color: #28a745;
        background: linear-gradient(45deg, #f8fff9, #ffffff);
    }
    
    .player-card.ausente {
        border-color: #dc3545;
        background: linear-gradient(45deg, #fff8f8, #ffffff);
    }
    
    .player-card.lesionado {
        border-color: #ffc107;
        background: linear-gradient(45deg, #fffbf0, #ffffff);
    }
    
    /* Controles más grandes para móvil */
    .stSelectbox > div > div {
        font-size: 16px !important;
        min-height: 48px !important;
    }
    
    .stTextInput > div > div > input {
        font-size: 16px !important;
        min-height: 45px !important;
    }
    
    /* Tabs optimizadas */
    .stTabs [data-baseweb="tab"] {
        height: 55px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        padding: 0 20px !important;
    }
    
    /* Responsive breakpoints */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        .lista-main-header h1 {
            font-size: 1.8rem;
        }
        
        .lista-main-header h2 {
            font-size: 1.1rem;
        }
        
        .player-card {
            padding: 14px;
        }
    }
    
    @media (max-width: 480px) {
        .lista-main-header {
            padding: 15px;
        }
        
        .lista-main-header h1 {
            font-size: 1.6rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # **HEADER PRINCIPAL LIMPIO - SIN BOTÓN VOLVER**
    st.markdown("""
    <div class="lista-main-header">
        <h1>📋 Pasar Lista - Universitario</h1>
        <h2>🏉 Sistema de Asistencia Optimizado</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # **INFO COMPACTA**
    st.info("💡 Sistema conectado  - Evite operaciones muy rápidas")
    
    # **TABS PRINCIPALES**
    tab1, tab2 = st.tabs(["📝 Pasar Lista", "📊 Ver Reportes"])
    
    with tab1:
        mostrar_pasar_lista()
    
    with tab2:
        mostrar_reportes()

def mostrar_pasar_lista():
    """Mostrar interfaz para pasar lista CON CACHE DE JUGADORES"""
    st.subheader("📱 Lista por Categoría")
    
    manager = AsistenciaManager()
    admin_manager = manager.admin_manager
    
    # **Cache de jugadores para evitar consultas repetidas**
    if 'cached_players' not in st.session_state or st.button("🔄 Actualizar Lista de Jugadores"):
        with st.spinner("📥 Cargando jugadores..."):
            df_players = admin_manager.get_all_players()
            st.session_state.cached_players = df_players
            st.session_state.players_cache_time = time.time()
    else:
        df_players = st.session_state.cached_players
        
        # Mostrar antigüedad del cache
        if 'players_cache_time' in st.session_state:
            cache_age = int((time.time() - st.session_state.players_cache_time) / 60)
            st.caption(f"📊 Lista de jugadores (actualizada hace {cache_age} min)")
    
    if df_players.empty:
        st.warning("⚠️ No hay jugadores registrados")
        return
    
    # **INTERFAZ OPTIMIZADA PARA MÓVIL**
    st.markdown("### ⚙️ Configuración de Lista")
    
    # Layout responsive: Stack en móvil, columnas en tablet
    # Detectar tamaño de pantalla usando session state
    if 'mobile_layout' not in st.session_state:
        st.session_state.mobile_layout = True
    
    # Toggle para cambiar layout
    layout_mode = st.radio(
        "Modo de vista:",
        ["📱 Móvil (Vertical)", "💻 Tablet (Horizontal)"],
        horizontal=True,
        key="layout_toggle"
    )
    
    mobile_mode = "Móvil" in layout_mode
    
    if mobile_mode:
        # Layout vertical para móvil
        fecha = st.date_input("📅 Fecha del Entrenamiento", value=date.today())
        
        categorias_disponibles = sorted(df_players['Categoria'].unique().tolist())
        categoria = st.selectbox(
            "🏆 Seleccionar Categoría", 
            categorias_disponibles,
            help="Elige la categoría de jugadores"
        )
        
        actividad = st.selectbox(
            "🏃 Tipo de Actividad",
            ["Entrenamiento", "Partido", "Preparación Física", "Reunión Técnica"],
            help="Selecciona el tipo de entrenamiento"
        )
    else:
        # Layout horizontal para tablet
        col1, col2 = st.columns(2)
        
        with col1:
            fecha = st.date_input("📅 Fecha", value=date.today())
            categorias_disponibles = sorted(df_players['Categoria'].unique().tolist())
            categoria = st.selectbox("🏆 Categoría", categorias_disponibles)
        
        with col2:
            actividad = st.selectbox(
                "🏃 Actividad",
                ["Entrenamiento", "Partido", "Preparación Física", "Reunión Técnica"]
            )
    
    # Filtrar jugadores activos de la categoría
    jugadores_categoria = df_players[
        (df_players['Categoria'] == categoria) & 
        (df_players['Estado'] == 'Activo')
    ].copy()
    
    if jugadores_categoria.empty:
        st.info(f"ℹ️ No hay jugadores activos en {categoria}")
        return
    
    # **LISTA SIMPLE Y GRANDE PARA TABLET**
    st.markdown(f"### 👥 {categoria} - {fecha.strftime('%d/%m/%Y')}")
    st.markdown(f"**Actividad:** {actividad} | **Total:** {len(jugadores_categoria)} jugadores")
    
    # Usar session state para mantener estado
    if 'attendance_data' not in st.session_state:
        st.session_state.attendance_data = {}
    
    # **INTERFAZ RESPONSIVA: Lista de asistencia optimizada**
    attendance_list = []
    
    # Opciones de asistencia con emojis más grandes
    estados_asistencia = {
        "✅ Presente": "Presente",
        "❌ Ausente": "Ausente", 
        "🩹 Lesionado": "Lesionado"
    }
    
    st.markdown("#### 📋 Lista de Jugadores")
    
    # Mostrar contador mientras se carga
    progress_text = f"Cargando {len(jugadores_categoria)} jugadores..."
    progress_bar = st.progress(0, text=progress_text)
    
    for idx, (_, player) in enumerate(jugadores_categoria.iterrows()):
        # Actualizar progress
        progress_bar.progress((idx + 1) / len(jugadores_categoria), 
                             text=f"Jugador {idx + 1} de {len(jugadores_categoria)}")
        
        dni = str(player['DNI'])
        nombre_completo = f"{player['Nombre']} {player['Apellido']}"
        
        # Obtener estado actual
        estado_default = st.session_state.attendance_data.get(dni, {}).get('estado', "✅ Presente")
        
        # Determinar clase CSS según estado
        estado_class = estados_asistencia.get(estado_default, "Presente").lower()
        
        # **CARD RESPONSIVA PARA CADA JUGADOR**
        st.markdown(f"""
        <div class="player-card {estado_class}">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div style="flex: 1;">
                    <h4 style="margin: 0; color: #2c3e50;">{nombre_completo}</h4>
                    <p style="margin: 0; color: #7f8c8d; font-size: 14px;">
                        DNI: {dni} | {player.get('Posicion', 'N/A')}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if mobile_mode:
            # Layout vertical para móvil
            estado_selected = st.selectbox(
                f"Estado de {player['Nombre']}",
                options=list(estados_asistencia.keys()),
                index=list(estados_asistencia.keys()).index(estado_default) if estado_default in estados_asistencia.keys() else 0,
                key=f"estado_{dni}",
                help="Selecciona el estado del jugador"
            )
            
            observaciones = st.text_input(
                f"Observaciones para {player['Nombre']}",
                value=st.session_state.attendance_data.get(dni, {}).get('observaciones', ''),
                key=f"obs_{dni}",
                placeholder="Ej: Llegó tarde, dolor rodilla...",
                help="Notas adicionales (opcional)"
            )
        else:
            # Layout horizontal para tablet
            col_status, col_obs = st.columns([1, 1])
            
            with col_status:
                estado_selected = st.selectbox(
                    "Estado",
                    options=list(estados_asistencia.keys()),
                    index=list(estados_asistencia.keys()).index(estado_default) if estado_default in estados_asistencia.keys() else 0,
                    key=f"estado_{dni}",
                    label_visibility="collapsed"
                )
            
            with col_obs:
                observaciones = st.text_input(
                    "Observaciones",
                    value=st.session_state.attendance_data.get(dni, {}).get('observaciones', ''),
                    key=f"obs_{dni}",
                    placeholder="Ej: Llegó tarde...",
                    label_visibility="collapsed"
                )
        
        # Guardar en session state
        if dni not in st.session_state.attendance_data:
            st.session_state.attendance_data[dni] = {}
        
        st.session_state.attendance_data[dni] = {
            'estado': estado_selected,
            'observaciones': observaciones
        }
        
        attendance_list.append({
            'dni': dni,
            'nombre': player['Nombre'],
            'apellido': player['Apellido'],
            'estado_asistencia': estados_asistencia[estado_selected],
            'observaciones': observaciones,
            'posicion': player.get('Posicion', 'N/A')
        })
        
        # Espaciado entre jugadores
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Limpiar progress bar
    progress_bar.empty()
    
    # **Resumen responsivo con métricas**
    presentes_count = sum(1 for p in attendance_list if p['estado_asistencia'] == 'Presente')
    ausentes_count = sum(1 for p in attendance_list if p['estado_asistencia'] == 'Ausente')
    lesionados_count = sum(1 for p in attendance_list if p['estado_asistencia'] == 'Lesionado')
    
    st.markdown("### 📊 Resumen de Asistencia")
    
    # Layout responsivo para métricas
    if mobile_mode:
        # Layout vertical para móvil
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3 style="margin: 0; color: #2c3e50;">👥 {}</h3>
                <p style="margin: 5px 0 0 0; color: #7f8c8d;">Total Jugadores</p>
            </div>
            """.format(len(attendance_list)), unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card" style="background: #d4edda; border-left: 4px solid #28a745;">
                <h3 style="margin: 0; color: #155724;">✅ {}</h3>
                <p style="margin: 5px 0 0 0; color: #155724;">Presentes</p>
            </div>
            """.format(presentes_count), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card" style="background: #f8d7da; border-left: 4px solid #dc3545;">
                <h3 style="margin: 0; color: #721c24;">❌ {}</h3>
                <p style="margin: 5px 0 0 0; color: #721c24;">Ausentes</p>
            </div>
            """.format(ausentes_count), unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card" style="background: #fff3cd; border-left: 4px solid #ffc107;">
                <h3 style="margin: 0; color: #856404;">🩹 {}</h3>
                <p style="margin: 5px 0 0 0; color: #856404;">Lesionados</p>
            </div>
            """.format(lesionados_count), unsafe_allow_html=True)
    else:
        # Layout horizontal para tablet
        col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
        
        with col_summary1:
            st.metric("👥 Total", len(attendance_list))
        with col_summary2:
            st.metric("✅ Presentes", presentes_count)
        with col_summary3:
            st.metric("❌ Ausentes", ausentes_count)
        with col_summary4:
            st.metric("🩹 Lesionados", lesionados_count)
    
    # Calcular porcentaje de participación
    activos_count = presentes_count + lesionados_count
    porcentaje_participacion = (activos_count / len(attendance_list) * 100) if len(attendance_list) > 0 else 0
    
    # Mostrar porcentaje con estilo
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
        font-size: 18px;
        font-weight: bold;
    ">
        📈 Participación Activa: {activos_count}/{len(attendance_list)} ({porcentaje_participacion:.1f}%)
        <br><small style="opacity: 0.8;">Incluye presentes + lesionados</small>
    </div>
    """, unsafe_allow_html=True)
    
    # **Botones responsivos para acción**
    st.markdown("### 🎯 Acciones Rápidas")
    
    if mobile_mode:
        # Layout vertical para móvil - botones más espaciados
        if st.button("💾 GUARDAR LISTA DE ASISTENCIA", use_container_width=True, type="primary"):
            with st.spinner("💾 Guardando en Google Sheets..."):
                if manager.save_attendance(attendance_list, fecha, categoria, actividad):
                    st.session_state.attendance_data = {}
                    st.success("¡Lista guardada exitosamente!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Expandir para botones rápidos
        with st.expander("⚡ Botones Rápidos", expanded=False):
            if st.button("👥 Marcar TODOS como PRESENTES", use_container_width=True):
                for player in jugadores_categoria.iterrows():
                    dni = str(player[1]['DNI'])
                    if dni not in st.session_state.attendance_data:
                        st.session_state.attendance_data[dni] = {}
                    st.session_state.attendance_data[dni]['estado'] = "✅ Presente"
                st.success(f"✅ {len(jugadores_categoria)} jugadores marcados como presentes")
                st.rerun()
            
            if st.button("❌ Marcar TODOS como AUSENTES", use_container_width=True):
                for player in jugadores_categoria.iterrows():
                    dni = str(player[1]['DNI'])
                    if dni not in st.session_state.attendance_data:
                        st.session_state.attendance_data[dni] = {}
                    st.session_state.attendance_data[dni]['estado'] = "❌ Ausente"
                st.warning(f"❌ {len(jugadores_categoria)} jugadores marcados como ausentes")
                st.rerun()
    else:
        # Layout horizontal para tablet
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ GUARDAR LISTA", use_container_width=True, type="primary"):
                with st.spinner("💾 Guardando en Google Sheets..."):
                    if manager.save_attendance(attendance_list, fecha, categoria, actividad):
                        st.session_state.attendance_data = {}
                        st.balloons()
                        st.rerun()
        
        with col2:
            if st.button("👥 TODOS PRESENTE", use_container_width=True):
                for player in jugadores_categoria.iterrows():
                    dni = str(player[1]['DNI'])
                    if dni not in st.session_state.attendance_data:
                        st.session_state.attendance_data[dni] = {}
                    st.session_state.attendance_data[dni]['estado'] = "✅ Presente"
                st.rerun()
        
        with col3:
            if st.button("❌ TODOS AUSENTE", use_container_width=True):
                for player in jugadores_categoria.iterrows():
                    dni = str(player[1]['DNI'])
                    if dni not in st.session_state.attendance_data:
                        st.session_state.attendance_data[dni] = {}
                    st.session_state.attendance_data[dni]['estado'] = "❌ Ausente"
                st.rerun()
    
    # **NUEVO: Botón para marcar lesionados**
    if st.button("🩹 Ver/Marcar Lesionados", use_container_width=True):
        st.session_state.show_injured_panel = not st.session_state.get('show_injured_panel', False)
        st.rerun()
    
    # **Panel especial para lesionados**
    if st.session_state.get('show_injured_panel', False):
        st.markdown("### 🩹 Panel de Lesionados")
        st.info("💡 Seleccione jugadores que están lesionados pero presentes en el entrenamiento")
        
        lesionados_cols = st.columns(3)
        for i, (idx, player) in enumerate(jugadores_categoria.iterrows()):
            dni = str(player['DNI'])
            col_idx = i % 3
            
            with lesionados_cols[col_idx]:
                if st.button(f"🩹 {player['Nombre']} {player['Apellido']}", key=f"lesion_{dni}"):
                    if dni not in st.session_state.attendance_data:
                        st.session_state.attendance_data[dni] = {}
                    st.session_state.attendance_data[dni]['estado'] = "🩹 Lesionado"
                    st.session_state.attendance_data[dni]['observaciones'] = "Marcado como lesionado"
                    st.rerun()

def mostrar_reportes():
    """Mostrar reportes de asistencia RESPONSIVE"""
    st.subheader("📊 Reportes de Asistencia")
    
    manager = AsistenciaManager()
    
    # **INICIALIZAR df_asistencias VACÍO AL PRINCIPIO**
    df_asistencias = pd.DataFrame()
    
    # Filtros para reportes
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_desde = st.date_input("📅 Desde", value=date.today())
    
    with col2:
        fecha_hasta = st.date_input("📅 Hasta", value=date.today())
    
    # **BOTÓN PARA GENERAR REPORTE**
    if st.button("🔍 Generar Reporte", use_container_width=True, type="primary"):
        with st.spinner("📊 Cargando datos de asistencia..."):
            # Obtener datos
            df_asistencias = manager.get_attendance_report(fecha_desde, fecha_hasta)
    
    # **VERIFICAR SI HAY DATOS ANTES DE PROCESAR**
    if df_asistencias.empty:
        st.info("ℹ️ Presiona 'Generar Reporte' para ver los datos de asistencia del período seleccionado")
        st.info("💡 Si no aparecen datos, verifica que existan registros de asistencia en las fechas seleccionadas")
        return
    
    # **PROCESAR DATOS SOLO SI EXISTEN**
    try:
        # Verificar formato de datos
        required_columns = ['Presente', 'Estado_Asistencia']
        available_columns = df_asistencias.columns.tolist()
        
        # Detectar formato (antiguo vs nuevo)
        if 'Estado_Asistencia' in available_columns:
            # **FORMATO NUEVO**
            st.success("✅ Datos en formato nuevo detectados")
            estado_column = 'Estado_Asistencia'
            
            # Calcular métricas
            total_registros = len(df_asistencias)
            total_presentes = len(df_asistencias[df_asistencias[estado_column] == 'Presente'])
            total_ausentes = len(df_asistencias[df_asistencias[estado_column] == 'Ausente'])
            total_lesionados = len(df_asistencias[df_asistencias[estado_column] == 'Lesionado'])
            
            # Participación = Presente + Lesionado (están físicamente)
            participacion_total = total_presentes + total_lesionados
            porcentaje_participacion = (participacion_total / total_registros * 100) if total_registros > 0 else 0
            porcentaje_presente_completo = (total_presentes / total_registros * 100) if total_registros > 0 else 0
            
        elif 'Presente' in available_columns:
            # **FORMATO ANTIGUO**
            st.warning("⚠️ Datos en formato antiguo detectados")
            estado_column = 'Presente'
            
            # Calcular métricas formato antiguo
            total_registros = len(df_asistencias)
            total_presentes = len(df_asistencias[df_asistencias[estado_column] == 'Presente'])
            total_ausentes = len(df_asistencias[df_asistencias[estado_column] == 'Ausente'])
            total_lesionados = 0  # No existe en formato antiguo
            
            participacion_total = total_presentes
            porcentaje_participacion = (total_presentes / total_registros * 100) if total_registros > 0 else 0
            porcentaje_presente_completo = porcentaje_participacion
            
        else:
            st.error("❌ Formato de datos no reconocido. Columnas disponibles: " + ", ".join(available_columns))
            return
        
        # **MOSTRAR MÉTRICAS RESPONSIVE**
        st.markdown("### 📊 Resumen del Período")
        
        # Detectar si es móvil
        is_mobile = st.session_state.get('mobile_mode', True)
        
        if is_mobile:
            # **MÓVIL: Cards verticales**
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 15px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white; text-align: center;">
                    <h2 style="margin: 0; font-size: 2.5em;">{total_registros}</h2>
                    <p style="margin: 5px 0 0 0; font-size: 1.1em;">📊 Total Registros</p>
                </div>
                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 20px; border-radius: 15px; color: white; text-align: center;">
                    <h2 style="margin: 0; font-size: 2.5em;">{total_presentes}</h2>
                    <p style="margin: 5px 0 0 0; font-size: 1.1em;">✅ Presentes ({porcentaje_presente_completo:.1f}%)</p>
                </div>
                <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); padding: 20px; border-radius: 15px; color: #333; text-align: center;">
                    <h2 style="margin: 0; font-size: 2.5em;">{total_ausentes}</h2>
                    <p style="margin: 5px 0 0 0; font-size: 1.1em;">❌ Ausentes</p>
                </div>
            """, unsafe_allow_html=True)
            
            if total_lesionados > 0:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); padding: 20px; border-radius: 15px; color: #333; text-align: center;">
                    <h2 style="margin: 0; font-size: 2.5em;">{total_lesionados}</h2>
                    <p style="margin: 5px 0 0 0; font-size: 1.1em;">🩹 Lesionados</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            # **TABLET/DESKTOP: Columnas tradicionales**
            if total_lesionados > 0:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Total Registros", total_registros)
                with col2:
                    st.metric("✅ Presentes", f"{total_presentes} ({porcentaje_presente_completo:.1f}%)")
                with col3:
                    st.metric("❌ Ausentes", total_ausentes)
                with col4:
                    st.metric("🩹 Lesionados", total_lesionados)
            else:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📊 Total Registros", total_registros)
                with col2:
                    st.metric("✅ Presentes", f"{total_presentes} ({porcentaje_presente_completo:.1f}%)")
                with col3:
                    st.metric("❌ Ausentes", total_ausentes)
        
        # **TABLA DE ASISTENCIAS**
        st.markdown("### 📋 Detalle de Asistencias")
        
        # Filtros adicionales
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Categoria' in df_asistencias.columns:
                categorias_disponibles = ["Todas"] + sorted(df_asistencias['Categoria'].unique().tolist())
                categoria_filter = st.selectbox("🏆 Filtrar por Categoría", categorias_disponibles)
        
        with col2:
            if 'Tipo_Actividad' in df_asistencias.columns:
                actividades_disponibles = ["Todas"] + sorted(df_asistencias['Tipo_Actividad'].unique().tolist())
                actividad_filter = st.selectbox("🏃 Filtrar por Actividad", actividades_disponibles)
        
        # Aplicar filtros
        df_filtered = df_asistencias.copy()
        
        if 'categoria_filter' in locals() and categoria_filter != "Todas":
            df_filtered = df_filtered[df_filtered['Categoria'] == categoria_filter]
        
        if 'actividad_filter' in locals() and actividad_filter != "Todas":
            df_filtered = df_filtered[df_filtered['Tipo_Actividad'] == actividad_filter]
        
        # Mostrar tabla
        if not df_filtered.empty:
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
            
            # **GRÁFICOS SOLO SI HAY DATOS**
            if len(df_filtered) > 0:
                # Gráfico por categoría
                if 'Categoria' in df_filtered.columns and len(df_filtered['Categoria'].unique()) > 1:
                    st.markdown("### 📊 Asistencia por Categoría")
                    try:
                        if 'Estado_Asistencia' in df_filtered.columns:
                            asistencia_categoria = df_filtered.groupby(['Categoria', 'Estado_Asistencia']).size().unstack(fill_value=0)
                        else:
                            asistencia_categoria = df_filtered.groupby(['Categoria', 'Presente']).size().unstack(fill_value=0)
                        
                        st.bar_chart(asistencia_categoria)
                    except Exception as e:
                        st.error(f"Error generando gráfico: {e}")
        else:
            st.info("ℹ️ No hay datos para mostrar con los filtros aplicados")
        
        # **DESCARGAR CSV - SOLO SI HAY DATOS**
        if not df_asistencias.empty:
            try:
                csv = df_asistencias.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar Reporte CSV",
                    data=csv,
                    file_name=f"reporte_asistencia_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error preparando descarga: {e}")
        
    except Exception as e:
        st.error(f"❌ Error procesando datos de asistencia: {e}")
        st.info("💡 Verifica que los datos en Google Sheets tengan el formato correcto")

if __name__ == "__main__":
    main_lista()