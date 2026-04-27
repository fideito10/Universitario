"""
Módulo de Reportes Médicos - Club Argentino de Rugby (CAR)
Interfaz de consulta para doctores - Solo lectura
Unión de datos: Base Central + Área Médica por DNI
"""


import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# =============================================================================
# 🔧 FUNCIONES AUXILIARES CORREGIDAS
# =============================================================================

def get_google_credentials():
    """
    Obtiene las credenciales de Google de forma segura desde st.secrets, Variables de Entorno (Railway) o archivo local
    """
    try:
        # 1. Intentar desde st.secrets
        if hasattr(st, 'secrets') and "google" in st.secrets:
            return dict(st.secrets["google"])
            
        # 2. Intentar desde Variables de Entorno (Railway)
        import os
        if os.getenv("STREAMLIT_GOOGLE_TYPE") or os.getenv("GOOGLE_TYPE"):
            prefix = "STREAMLIT_GOOGLE_" if os.getenv("STREAMLIT_GOOGLE_TYPE") else "GOOGLE_"
            creds = {
                "type": os.getenv(f"{prefix}TYPE"),
                "project_id": os.getenv(f"{prefix}PROJECT_ID"),
                "private_key_id": os.getenv(f"{prefix}PRIVATE_KEY_ID"),
                "private_key": os.getenv(f"{prefix}PRIVATE_KEY", "").replace('\\n', '\n'),
                "client_email": os.getenv(f"{prefix}CLIENT_EMAIL"),
                "client_id": os.getenv(f"{prefix}CLIENT_ID"),
                "auth_uri": os.getenv(f"{prefix}AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv(f"{prefix}TOKEN_URI", "https://oauth2.googleapis.com/token")
            }
            return creds

        # 3. Intentar desde archivos locales
        import json
        possible_paths = [
            "credentials/service_account.json",
            "../credentials/service_account.json",
            "service_account.json"
        ]
        
        for cred_path in possible_paths:
            if os.path.exists(cred_path):
                with open(cred_path) as f:
                    return json.load(f)
                    
        return None
    except Exception:
        return None

def conectar_base_central():
    """Conectar a Base Central - puede ser una hoja diferente"""
    try:
        try:
            from src.modules.areamedica import read_google_sheet_with_headers
        except ImportError:
            from areamedica import read_google_sheet_with_headers

        # Usar el ID correcto de la hoja base de jugadores
        result = read_google_sheet_with_headers(
            sheet_id='1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw',
            worksheet_name=None  # usar primera hoja o especifica si es necesario
        )
        if not result or not result.get('success'):
            error_msg = result.get('error', 'Error desconocido') if result else 'Sin respuesta'
            st.error(f"❌ Error conectando a Base Central: {error_msg}")
            return []

        data = result.get('data', [])

        if not data:
            st.warning("⚠️ Base Central sin datos")
            return []

        # Procesar datos para formato de jugadores
        jugadores = []
        for registro in data:
            # Unir Nombre y Apellido para el campo 'nombre'
            if 'Nombre' in registro and 'Apellido' in registro:
                nombre = (registro.get('Nombre', '').strip() + ' ' + registro.get('Apellido', '').strip()).strip()
            else:
                nombre = registro.get('Nombre y Apellido', '').strip()
            jugador = {
                'nombre': nombre,
                'dni': str(registro.get('DNI', registro.get('dni', ''))).strip(),
                'categoria': registro.get('Categoria', registro.get('categoria', registro.get('División', 'Sin Categoría'))).strip(),
                'posicion': registro.get('Posicion', registro.get('Posición', registro.get('posicion', ''))).strip(),  # 👈 AGREGADO 'Posicion' sin tilde
                'estado': registro.get('Estado', registro.get('estado', 'Activo')).strip(),
                'telefono': registro.get('Telefono', registro.get('Teléfono', registro.get('telefono', ''))).strip(),  # 👈 AGREGADO 'Telefono' sin tilde
                'email': registro.get('Email', registro.get('email', '')).strip()
            }
            if jugador['nombre'] and jugador['dni']:
                jugadores.append(jugador)

        
        return jugadores

    except ImportError:
        st.error("❌ No se puede importar areamedica.py")
        return []
    except Exception as e:
        st.error(f"❌ Error en conectar_base_central: {str(e)}")
        return []

def normalizar_categoria(cat):
    """Normaliza el nombre de la categoría para evitar duplicados por mayúsculas/minúsculas y espacios."""
    if not cat:
        return "Sin Categoría"
    return cat.strip().upper() 
    
def conectar_area_medica():
    """Conectar a Área Médica con manejo mejorado de errores"""
    try:
        st.info
        
        try:
            from src.modules.areamedica import read_google_sheet_with_headers
        except ImportError:
            from areamedica import read_google_sheet_with_headers
            st.success
        except ImportError:
            st.warning("⚠️ Módulo areamedica.py no encontrado - Continuando sin datos médicos")
            return []
        
        # Usar el ID correcto de la hoja de historial clínico
        result = read_google_sheet_with_headers(
            sheet_id='1ham2WSMQa3eEv0V0TtHcAa55R3WLGoBje6pSOoNxcBQ',
            worksheet_name=None  # usa la primera hoja o especifica si es necesario
        )
        
        if not result:
            st.warning("⚠️ Sin respuesta del módulo médico")
            return []
        
        if not result.get('success'):
            error_msg = result.get('error', 'Error desconocido')
            st.warning(f"⚠️ Error en Área Médica: {error_msg}")
            return []
        
        medical_data = result.get('data', [])
        st.success
        return medical_data
            
    except Exception as e:
        st.warning(f"⚠️ Área Médica no disponible: {e}")
        return []

# AGREGAR ESTAS FUNCIONES QUE FALTAN:

def normalizar_dni(dni):
    """Normalizar DNI para comparación"""
    if not dni:
        return ""
    return str(dni).replace('.', '').replace('-', '').replace(' ', '').strip()

def obtener_historial_por_dni(dni, datos_medicos):
    """Obtener historial médico por DNI"""
    dni_normalizado = normalizar_dni(dni)
    if not dni_normalizado:
        return []
    
    historial = []
    for registro in datos_medicos:
        dni_registro = normalizar_dni(registro.get('DNI', registro.get('Dni', '')))
        if dni_registro and dni_registro == dni_normalizado:
            historial.append(registro)
    
    # Ordenar por fecha (más reciente primero)
    historial.sort(
        key=lambda x: x.get('Fecha de Atención', x.get('Marca temporal', '1900-01-01')),
        reverse=True
    )
    return historial

def diagnosticar_sistema():
    """Función de diagnóstico completo del sistema"""
    st.markdown("## 🔧 **Diagnóstico del Sistema**")
    
    # 1. Verificar secrets
    st.markdown("### 1. 📋 Verificación de Secrets")
    try:
        if hasattr(st, 'secrets'):
            st.success
            
            if "google_credentials" in st.secrets:
                st.success
                
                # Verificar campos
                creds = st.secrets["google_credentials"]
                required_fields = ["type", "project_id", "private_key", "client_email"]
                missing = [f for f in required_fields if f not in creds]
                
                if not missing:
                    st.success("✅ Todos los campos obligatorios presentes")
                else:
                    st.error(f"❌ Campos faltantes: {missing}")
                    
            else:
                st.error("❌ google_credentials NO encontradas en secrets")
        else:
            st.error("❌ st.secrets no disponible")
    except Exception as e:
        st.error(f"❌ Error verificando secrets: {e}")
    
    # 2. Verificar librerías
    st.markdown("### 2. 📚 Verificación de Librerías")
    try:
        import gspread
        st.success("✅ gspread instalado")
    except ImportError:
        st.error("❌ gspread NO instalado")
        st.error("💡 Ejecuta: pip install gspread")
    
    try:
        from google.oauth2.service_account import Credentials
        st.success("✅ google-auth instalado")
    except ImportError:
        st.error("❌ google-auth NO instalado")
        st.error("💡 Ejecuta: pip install google-auth google-auth-oauthlib")
    
    # 3. Verificar módulos locales
    st.markdown("### 3. 🏥 Verificación de Módulos")
    try:
        from areamedica import read_google_sheet_with_headers
        st.success("✅ Módulo areamedica disponible")
    except ImportError:
        st.warning("⚠️ Módulo areamedica NO disponible")
    
    # 4. Test de conexión básica
    st.markdown("### 4. 🌐 Test de Conexión")
    if st.button("🧪 Probar Conexión a Google Sheets"):
        with st.spinner("Probando conexión..."):
            jugadores = conectar_base_central()
            if jugadores:
                st.success(f"✅ Conexión exitosa: {len(jugadores)} jugadores cargados")
                
                # Mostrar muestra
                st.markdown("**🔍 Muestra de datos:**")
                for i, jugador in enumerate(jugadores[:3]):
                    st.write(f"{i+1}. {jugador['nombre']} - {jugador['categoria']} - DNI: {jugador['dni']}")
            else:
                st.error("❌ Conexión fallida")

  
def estado_entrenamiento_actual(historial_medico):
    """
    Devuelve 'Activo', 'Diferenciado' o 'Inactivo' según el último registro médico.
    """
    if not historial_medico:
        return None
    ultimo = historial_medico[0]
    puede_entrenar = ultimo.get('¿Puede participar en entrenamientos?', '').strip().lower()
    if puede_entrenar == 'si' or puede_entrenar == 'sí':
        return 'Activo'
    elif puede_entrenar == 'solo con entrenamiento diferenciado':
        return 'Diferenciado'
    elif puede_entrenar == 'no':
        return 'Inactivo'
    return None    



def main_reporte_medico():
    """Función principal - Interfaz simplificada con diagnóstico"""
    
    # 1. CARGAR DATOS (Esto faltaba y es crucial para que funcionen los filtros)
    with st.spinner("🔄 Cargando base de datos de jugadores y reportes médicos..."):
         jugadores = conectar_base_central()
         datos_medicos = conectar_area_medica()

    # 🎨 CSS personalizado
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .filter-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border-left: 5px solid #2a5298;
    }
    .resumen-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #28a745;
    }
    .stat-card {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 🏥 Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🏥 Consulta Médica</h1>
    </div>
    """, unsafe_allow_html=True)
    


    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.markdown("### 🔍 **Filtros de Búsqueda**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtro por categoría
        if jugadores:
            categorias_jugadores = [
                normalizar_categoria(j.get('categoria', 'Sin Categoría'))
                for j in jugadores if j.get('categoria')
            ]
            categorias_disponibles = sorted(list(set(categorias_jugadores)))
        else:
            categorias_disponibles = []

        categoria_seleccionada = st.selectbox(
            "**📂 Categoría:**",
            options=['Todas'] + categorias_disponibles,
            key="filtro_categoria"
        )
        
    with col2:
        # Filtro por nombre
        jugadores_filtrados = []
        if jugadores:
            if categoria_seleccionada != 'Todas':
                jugadores_filtrados = [
                    j for j in jugadores
                    if normalizar_categoria(j.get('categoria', 'Sin Categoría')) == categoria_seleccionada
                ]
            else:
                jugadores_filtrados = jugadores

        nombres_disponibles = sorted([
            j.get('nombre', '').strip()
            for j in jugadores_filtrados if j.get('nombre')
        ])
        
        jugador_seleccionado = st.selectbox(
            "**👤 Nombre y Apellido:**",
            options=['Seleccionar jugador...'] + nombres_disponibles,
            key="filtro_jugador"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 🎯 Encontrar jugador seleccionado en la lista de jugadores (Base Central)
    jugador_actual = None
    if jugador_seleccionado != 'Seleccionar jugador...':
        for jugador in jugadores:
            if jugador.get('nombre', '').strip() == jugador_seleccionado:
                jugador_actual = jugador
                break
    
    
    # Botón para cargar nuevo reporte
    if jugador_seleccionado != 'Seleccionar jugador...':
        if st.button("➕ Nuevo reporte", key="nuevo_reporte"):
            st.session_state['mostrar_formulario_reporte'] = True

    # Mostrar formulario si el botón fue presionado
    if st.session_state.get('mostrar_formulario_reporte', False) and jugador_seleccionado != 'Seleccionar jugador...':
        st.markdown("### 📝 Nuevo Reporte Médico")
        with st.form("formulario_reporte_medico"):
            fecha = st.date_input("Fecha de Atención", value=datetime.today())
            nombre_doctor = st.text_input("Nombre del Doctor")
            tipo_lesion = st.selectbox(
                "Tipo de Lesión",
                [
                    "Esguince",
                    "Contractura muscular",
                    "Desgarro muscular",
                    "Fractura",
                    "Luxación",
                    "Contusión",
                    "Lesión ligamentosa",
                    "Lesión meniscal",
                    "Conmoción",
                    "Corte / Herida",
                    "Otro"
                ]
            )
            severidad = st.selectbox("Severidad de la Lesión", ["Leve", "Moderada", "Grave"])
            cuando_ocurrio = st.date_input("¿Cuándo ocurrió la lesión?", value=datetime.today())
            como_ocurrio = st.text_area("¿Cómo ocurrió la lesión?")
            parte_afectada = st.selectbox(
                "Parte del Cuerpo Afectada",
                [
                    "Cabeza",
                    "Cuello",
                    "Hombro",
                    "Brazo",
                    "Codo",
                    "Antebrazo",
                    "Muñeca",
                    "Mano",
                    "Dedos",
                    "Pecho",
                    "Espalda",
                    "Cadera",
                    "Muslo",
                    "Rodilla",
                    "Pierna",
                    "Tobillo",
                    "Pie",
                    "Costillas",
                    "Columna",
                    "Oreja",
                    "Ojo",
                    "Nariz",
                    "Otro"
                ]
            )
            puede_entrenar = st.selectbox("¿Puede participar en entrenamientos?", ["Sí", "No", "Solo con entrenamiento diferenciado"])
            requiere_cirugia = st.selectbox("¿Requiere Cirugía?", ["No", "Sí"])
            proxima_evaluacion = st.date_input("Fecha de Próxima Evaluación", value=datetime.today())
            estado_caso = st.text_input("Estado del Caso")
            tratamiento = st.text_area("Tratamiento Prescrito")
            observaciones = st.text_area("Observaciones Adicionales")
            submit = st.form_submit_button("Guardar reporte")

            if submit:
                # --- GUARDAR REPORTE EN GOOGLE SHEETS ---
                categoria_jugador = jugador_actual.get('categoria', 'Sin Categoría')
                posicion_jugador = jugador_actual.get('posicion', 'No especificada')
                nombre_jugador = jugador_actual.get('nombre', '')
                dni_jugador = jugador_actual.get('dni', '')
                
                # Marca temporal actual
                marca_temporal = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                nuevo_reporte = [
                    marca_temporal,                # Marca temporal
                    nombre_doctor,                 # Nombre del Doctor
                    str(fecha),                    # Fecha
                    nombre_jugador,                # Nombre y Apellido
                    dni_jugador,                   # Dni
                    categoria_jugador,             # Categoría
                    posicion_jugador,              # Posición del jugador
                    tipo_lesion,                   # Tipo de Lesión
                    parte_afectada,                # Parte del Cuerpo Afectada
                    severidad,                     # Severidad de la Lesión
                    str(cuando_ocurrio),                # ¿Cuándo ocurrió la lesión?
                    como_ocurrio,                  # ¿Cómo ocurrió la lesión?
                    requiere_cirugia,              # ¿Requiere Cirugía?
                    puede_entrenar,                # ¿Puede participar en entrenamientos?
                    str(proxima_evaluacion),       # Fecha de Próxima Evaluación
                    observaciones,                 # Observaciones Adicionales
                    tratamiento                    # Medicamentos recetados (si corresponde)
                ]
                google_creds = get_google_credentials()
        # Guardar el reporte
        if google_creds:
            try:
                try:
                    from src.modules.areamedica import append_google_sheet_row
                except ImportError:
                    from areamedica import append_google_sheet_row
                append_google_sheet_row(
                    sheet_id='1ham2WSMQa3eEv0V0TtHcAa55R3WLGoBje6pSOoNxcBQ',
                    worksheet_name='Respuestas de formulario 1',
                    row_data=nuevo_reporte,
                    credentials_dict=google_creds
                )
                st.success("✅ Reporte guardado en Google Sheets")
                # Recargar datos médicos para mostrar el historial actualizado
                datos_medicos = conectar_area_medica()
            except Exception as e:
                st.error(f"❌ Error guardando reporte: {e}")
        else:
            st.error("❌ No se pudo obtener credenciales de Google")
        # Ocultar el formulario
        st.session_state['mostrar_formulario_reporte'] = False



    if jugador_actual:
        dni_jugador = jugador_actual.get('dni', '').strip()
        historial_medico = obtener_historial_por_dni(dni_jugador, datos_medicos)
        
        st.markdown('<div class="resumen-card">', unsafe_allow_html=True)
        
        nombre_jugador = jugador_actual.get('nombre', 'Sin Nombre')
        categoria_jugador = jugador_actual.get('categoria', 'Sin Categoría')
        posicion_jugador = jugador_actual.get('posicion', 'No especificada')
        estado_jugador = jugador_actual.get('estado', 'Activo')
        telefono_jugador = jugador_actual.get('telefono', '')
        email_jugador = jugador_actual.get('email', '')
        
        
        
       
        st.markdown(f"<h2 style='text-align:left; color:#1e3c72;'>{nombre_jugador}</h2>", unsafe_allow_html=True)
        estado_entrenamiento = estado_entrenamiento_actual(historial_medico)
        if estado_entrenamiento == 'Activo':
            st.markdown("### Estado: ✅ Activo (Apto para entrenar)")
        elif estado_entrenamiento == 'Diferenciado':
            st.markdown("### Estado: 🟡 Diferenciado (Solo entrenamiento diferenciado)")
        elif estado_entrenamiento == 'Inactivo':
            st.markdown("### Estado: 🔴 Inactivo (No apto para entrenar)")
        else:
            st.markdown(f"### Estado: {'✅ Activo' if estado_jugador == 'Activo' else '🔴 Inactivo'} (sin registro médico reciente)")

        st.markdown("---")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.caption("Posición")
            st.markdown(f"#### {posicion_jugador}")
            
        with c2:
            st.caption("Documento")
            st.markdown(f"#### {dni_jugador}")
        
        with c3:
            st.caption("Teléfono")
            st.markdown(f"#### {telefono_jugador if telefono_jugador else '—'}")

        with c4:
            st.caption("Email")
            st.markdown(f"#### {email_jugador if email_jugador else '—'}")
            
        st.markdown("---")
            
        if historial_medico:
            ultimo_registro = historial_medico[0]
            col_hist1,= st.columns(1)
            with col_hist1:
                st.markdown("#### 📋 **Historial Resumido**")
                st.markdown(f"**Total de registros:** {len(historial_medico)}")
                lesiones = [h.get('Tipo de Lesión', '') for h in historial_medico if h.get('Tipo de Lesión')]
                if lesiones:
                    lesion_mas_frecuente = max(set(lesiones), key=lesiones.count)
                    st.markdown(f"**Lesión más frecuente:** {lesion_mas_frecuente}")
            st.markdown("#### 📋 **Registros Detallados**")
            for i, registro in enumerate(historial_medico[:3]):
                fecha = registro.get('Fecha de Atención', registro.get('Marca temporal', 'Sin fecha'))
                diagnostico = registro.get('Tipo de Lesión', 'Sin diagnóstico')
                severidad = registro.get('Severidad de la Lesión', 'No especificada')
                
                # 🎨 TÍTULO MEJORADO CON ÍCONOS Y COLOR SEGÚN SEVERIDAD
                icono_severidad = {
                    'Leve': '🟢',
                    'Moderada': '🟡', 
                    'Grave': '🔴'
                }.get(severidad, '⚪')
                
                titulo_expander = f"{icono_severidad} **{fecha}** • {diagnostico} • *{severidad}*"
                
                with st.expander(titulo_expander, expanded=(i==0)):
                    col_det1, col_det2 = st.columns(2)
                    with col_det1:
                        st.markdown(f"""
                        **👨‍⚕️ Doctor:** {registro.get('Nombre del Doctor', 'No especificado')}  
                        **🩺 Diagnóstico:** {diagnostico}  
                        **⚠️ Severidad:** {registro.get('Severidad de la Lesión', 'No especificada')}  
                        **🎯 Parte Afectada:** {registro.get('Parte del Cuerpo Afectada', 'No especificada')}
                        """)
                    with col_det2:
                        st.markdown(f"""
                        **🏃‍♂️ Puede Entrenar:** {registro.get('¿Puede participar en entrenamientos?', 'No especificado')}  
                        **🔪 Requiere Cirugía:** {registro.get('¿Requiere Cirugía?', 'No especificado')}  
                        **📅 Próx. Evaluación:** {registro.get('Fecha de Próxima Evaluación', 'No programada')}  
                        **📊 Estado Caso:** {registro.get('Estado del Caso', 'No especificado')}
                        """)
                    if registro.get('Tratamiento Prescrito'):
                        st.markdown(f"**💊 Tratamiento:** {registro['Tratamiento Prescrito']}")
                    if registro.get('Observaciones Adicionales'):
                        st.markdown(f"**📝 Observaciones:** {registro['Observaciones Adicionales']}")
        else:
            st.info("📋 **Sin registros médicos previos** - Jugador sin historial clínico registrado")
        st.markdown('</div>', unsafe_allow_html=True)


    # Footer informativo
    st.markdown("---")
    st.caption("📊 **Fuentes de datos:** Base Central (jugadores) + Área Médica (historiales) | 🔄 Actualización en tiempo real")

# Ejecutar si es llamado directamente
if __name__ == "__main__":
    main_reporte_medico()