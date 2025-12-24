"""
Interfaz de usuario para Google Sheets Sync
Integración completa con Streamlit para CAR Rugby Club
"""

import streamlit as st
from google_sheets_sync import GoogleSheetsCAR, save_sync_config, load_sync_config
from utils import save_medical_data, save_nutrition_data, load_json_data
import pandas as pd
from datetime import datetime
import json

def google_sheets_page():
    """Página principal de Google Sheets"""
    st.markdown("""
    <div class="main-header">
        <h1>🔗 Sincronización Google Sheets</h1>
        <h3>Conectar hojas de cálculo de profesionales</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar Google Sheets
    gs = GoogleSheetsCAR()
    
    if gs.client is None:
        show_credentials_setup()
        return
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏥 Sincronizar Médico", 
        "🥗 Sincronizar Nutrición",
        "💪 Sincronizar Fuerza",
        "🏃 Sincronizar Campo", 
        "📊 Estado de Conexiones",
        "⚙️ Configuración"
    ])
    
    with tab1:
        medical_sync_interface(gs)
    
    with tab2:
        nutrition_sync_interface(gs)
    
    with tab3:
        strength_sync_interface(gs)
    
    with tab4:
        field_sync_interface(gs)
    
    with tab5:
        connection_status(gs)
    
    with tab6:
        sync_configuration(gs)

def show_credentials_setup():
    """Mostrar instrucciones para configurar credenciales"""
    st.error("🔐 Configuración de Google Sheets requerida")
    
    with st.expander("📋 Instrucciones de Configuración", expanded=True):
        st.markdown("""
        ### Pasos para configurar Google Sheets:
        
        1. **Ir a Google Cloud Console:**
           - Visita: https://console.cloud.google.com/
        
        2. **Crear nuevo proyecto:**
           - Nombre: "CAR Rugby Club"
        
        3. **Habilitar APIs:**
           - Google Sheets API
           - Google Drive API
        
        4. **Crear credenciales:**
           - Tipo: Service Account
           - Descargar archivo JSON
        
        5. **Colocar archivo:**
           - Renombrar a: `car_google_credentials.json`
           - Ubicar en: `c:\\Users\\dell\\Desktop\\Car\\`
        
        6. **Compartir hojas:**
           - Agregar email del service account
           - Dar permisos de "Editor"
        """)
    
    # Opción para subir credenciales
    uploaded_creds = st.file_uploader(
        "📁 Subir archivo de credenciales JSON",
        type=['json'],
        help="Archivo descargado de Google Cloud Console"
    )
    
    if uploaded_creds is not None:
        # Guardar credenciales
        with open("car_google_credentials.json", "wb") as f:
            f.write(uploaded_creds.read())
        st.success("✅ Credenciales guardadas. Recarga la página.")
        st.rerun()

def medical_sync_interface(gs):
    """Interfaz para sincronizar datos médicos"""
    st.subheader("🏥 Sincronización Área Médica")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sheet_url = st.text_input(
            "🔗 URL de Google Sheets (Médico):",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Pega aquí la URL completa de tu Google Sheet"
        )
    
    with col2:
        doctor_name = st.selectbox(
            "👨‍⚕️ Doctor:",
            ["Dr. García", "Dr. Fernández", "Dr. Martínez", "Otro"]
        )
        
        if doctor_name == "Otro":
            doctor_name = st.text_input("Nombre del doctor:")
    
    # Probar conexión
    if sheet_url:
        test_btn = st.button("🔍 Probar Conexión", key="test_medical")
        
        if test_btn:
            success, message = gs.test_connection(sheet_url)
            if success:
                st.success(f"✅ {message}")
                
                # Obtener lista de hojas
                success_ws, worksheets = gs.get_worksheets(sheet_url)
                if success_ws:
                    worksheet = st.selectbox(
                        "📋 Seleccionar hoja de trabajo:",
                        [""] + worksheets,
                        key="medical_worksheet"
                    )
                    
                    if worksheet:
                        # Vista previa de datos
                        success_data, data = gs.get_sheet_data(sheet_url, worksheet)
                        if success_data:
                            st.write("👀 Vista previa de datos:")
                            st.dataframe(data.head())
                            
                            # Botón para sincronizar
                            if st.button("🔄 Sincronizar Datos Médicos", key="sync_medical"):
                                sync_medical_data(gs, sheet_url, doctor_name, worksheet)
            else:
                st.error(f"❌ {message}")

def nutrition_sync_interface(gs):
    """Interfaz para sincronizar datos nutricionales"""
    st.subheader("🥗 Sincronización Área Nutrición")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sheet_url = st.text_input(
            "🔗 URL de Google Sheets (Nutrición):",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Pega aquí la URL completa de tu Google Sheet",
            key="nutrition_url"
        )
    
    with col2:
        nutritionist = st.selectbox(
            "🥗 Nutricionista:",
            ["Lic. María López", "Lic. Ana García", "Lic. Juan Pérez", "Otro"],
            key="nutritionist_select"
        )
        
        if nutritionist == "Otro":
            nutritionist = st.text_input("Nombre del nutricionista:", key="custom_nutritionist")
    
    # Similar al médico pero para nutrición
    if sheet_url:
        test_btn = st.button("🔍 Probar Conexión", key="test_nutrition")
        
        if test_btn:
            success, message = gs.test_connection(sheet_url)
            if success:
                st.success(f"✅ {message}")
                
                success_ws, worksheets = gs.get_worksheets(sheet_url)
                if success_ws:
                    worksheet = st.selectbox(
                        "📋 Seleccionar hoja de trabajo:",
                        [""] + worksheets,
                        key="nutrition_worksheet"
                    )
                    
                    if worksheet:
                        success_data, data = gs.get_sheet_data(sheet_url, worksheet)
                        if success_data:
                            st.write("👀 Vista previa de datos:")
                            st.dataframe(data.head())
                            
                            if st.button("🔄 Sincronizar Datos Nutricionales", key="sync_nutrition"):
                                sync_nutrition_data(gs, sheet_url, nutritionist, worksheet)
            else:
                st.error(f"❌ {message}")

def sync_medical_data(gs, sheet_url, doctor_name, worksheet):
    """Ejecutar sincronización de datos médicos"""
    with st.spinner("🔄 Sincronizando datos médicos..."):
        success, records = gs.sync_medical_data(sheet_url, doctor_name, worksheet)
        
        if success:
            if records:
                # Cargar datos existentes
                existing_data = load_json_data('medical_records.json', {'injuries': []})
                
                # Agregar nuevos registros
                existing_data['injuries'].extend(records)
                
                # Guardar usando la función de utils
                with open('medical_records.json', 'w') as f:
                    json.dump(existing_data, f, indent=2)
                
                st.success(f"✅ {len(records)} registros médicos sincronizados correctamente!")
                
                # Mostrar resumen
                with st.expander("📊 Resumen de sincronización"):
                    df_summary = pd.DataFrame(records)
                    st.dataframe(df_summary[['player_name', 'injury_type', 'severity', 'doctor']])
                
                # Guardar configuración
                config = load_sync_config()
                config['medical_sheets'].append({
                    'url': sheet_url,
                    'doctor': doctor_name,
                    'worksheet': worksheet,
                    'last_sync': datetime.now().isoformat()
                })
                save_sync_config(config)
                
                st.balloons()
            else:
                st.warning("⚠️ No se encontraron datos para sincronizar")
        else:
            st.error(f"❌ Error en sincronización: {records}")

def sync_nutrition_data(gs, sheet_url, nutritionist, worksheet):
    """Ejecutar sincronización de datos nutricionales"""
    with st.spinner("🔄 Sincronizando datos nutricionales..."):
        success, records = gs.sync_nutrition_data(sheet_url, nutritionist, worksheet)
        
        if success:
            if records:
                # Cargar datos existentes
                existing_data = load_json_data('nutrition_records.json', {'meal_plans': []})
                
                # Agregar nuevos registros
                existing_data['meal_plans'].extend(records)
                
                # Guardar usando la función de utils
                with open('nutrition_records.json', 'w') as f:
                    json.dump(existing_data, f, indent=2)
                
                st.success(f"✅ {len(records)} registros nutricionales sincronizados correctamente!")
                
                # Mostrar resumen
                with st.expander("📊 Resumen de sincronización"):
                    df_summary = pd.DataFrame(records)
                    st.dataframe(df_summary[['player_name', 'plan_type', 'calories_target', 'nutritionist']])
                
                # Guardar configuración
                config = load_sync_config()
                config['nutrition_sheets'].append({
                    'url': sheet_url,
                    'nutritionist': nutritionist,
                    'worksheet': worksheet,
                    'last_sync': datetime.now().isoformat()
                })
                save_sync_config(config)
                
                st.balloons()
            else:
                st.warning("⚠️ No se encontraron datos para sincronizar")
        else:
            st.error(f"❌ Error en sincronización: {records}")

def strength_sync_interface(gs):
    """Interfaz para sincronizar datos de tests de fuerza"""
    st.subheader("💪 Sincronización Tests de Fuerza")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sheet_url = st.text_input(
            "🔗 URL de Google Sheets (Tests de Fuerza):",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Pega aquí la URL completa de tu Google Sheet",
            key="strength_url"
        )
    
    with col2:
        trainer = st.selectbox(
            "💪 Preparador Físico:",
            ["Prof. García", "Prof. Martínez", "Prof. López", "Otro"],
            key="trainer_select"
        )
        
        if trainer == "Otro":
            trainer = st.text_input("Nombre del preparador:", key="custom_trainer")
    
    if sheet_url:
        test_btn = st.button("🔍 Probar Conexión", key="test_strength")
        
        if test_btn:
            success, message = gs.test_connection(sheet_url)
            if success:
                st.success(f"✅ {message}")
                
                success_ws, worksheets = gs.get_worksheets(sheet_url)
                if success_ws:
                    worksheet = st.selectbox(
                        "📋 Seleccionar hoja de trabajo:",
                        [""] + worksheets,
                        key="strength_worksheet"
                    )
                    
                    if worksheet:
                        success_data, data = gs.get_sheet_data(sheet_url, worksheet)
                        if success_data:
                            st.write("👀 Vista previa de datos:")
                            st.dataframe(data.head())
                            
                            if st.button("🔄 Sincronizar Tests de Fuerza", key="sync_strength"):
                                sync_strength_data(gs, sheet_url, trainer, worksheet)
            else:
                st.error(f"❌ {message}")

def field_sync_interface(gs):
    """Interfaz para sincronizar datos de tests de campo"""
    st.subheader("🏃 Sincronización Tests de Campo")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sheet_url = st.text_input(
            "🔗 URL de Google Sheets (Tests de Campo):",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Pega aquí la URL completa de tu Google Sheet",
            key="field_url"
        )
    
    with col2:
        trainer = st.selectbox(
            "🏃 Preparador Físico:",
            ["Prof. García", "Prof. Martínez", "Prof. López", "Otro"],
            key="field_trainer_select"
        )
        
        if trainer == "Otro":
            trainer = st.text_input("Nombre del preparador:", key="custom_field_trainer")
    
    if sheet_url:
        test_btn = st.button("🔍 Probar Conexión", key="test_field")
        
        if test_btn:
            success, message = gs.test_connection(sheet_url)
            if success:
                st.success(f"✅ {message}")
                
                success_ws, worksheets = gs.get_worksheets(sheet_url)
                if success_ws:
                    worksheet = st.selectbox(
                        "📋 Seleccionar hoja de trabajo:",
                        [""] + worksheets,
                        key="field_worksheet"
                    )
                    
                    if worksheet:
                        success_data, data = gs.get_sheet_data(sheet_url, worksheet)
                        if success_data:
                            st.write("👀 Vista previa de datos:")
                            st.dataframe(data.head())
                            
                            if st.button("🔄 Sincronizar Tests de Campo", key="sync_field"):
                                sync_field_data(gs, sheet_url, trainer, worksheet)
            else:
                st.error(f"❌ {message}")

def sync_strength_data(gs, sheet_url, trainer, worksheet):
    """Ejecutar sincronización de datos de tests de fuerza"""
    with st.spinner("🔄 Sincronizando tests de fuerza..."):
        success, records = gs.sync_strength_data(sheet_url, trainer, worksheet)
        
        if success:
            if records:
                # Cargar datos existentes
                existing_data = load_json_data('strength_tests.json', {'tests': []})
                
                # Agregar nuevos registros
                existing_data['tests'].extend(records)
                
                # Guardar
                with open('strength_tests.json', 'w') as f:
                    json.dump(existing_data, f, indent=2)
                
                st.success(f"✅ {len(records)} tests de fuerza sincronizados correctamente!")
                
                # Mostrar resumen
                with st.expander("📊 Resumen de sincronización"):
                    df_summary = pd.DataFrame(records)
                    st.dataframe(df_summary[['player_name', 'test_type', 'weight', 'one_rm_estimated']])
                
                # Guardar configuración
                config = load_sync_config()
                config['strength_sheets'].append({
                    'url': sheet_url,
                    'trainer': trainer,
                    'worksheet': worksheet,
                    'last_sync': datetime.now().isoformat()
                })
                save_sync_config(config)
                
                st.balloons()
            else:
                st.warning("⚠️ No se encontraron datos para sincronizar")
        else:
            st.error(f"❌ Error en sincronización: {records}")

def sync_field_data(gs, sheet_url, trainer, worksheet):
    """Ejecutar sincronización de datos de tests de campo"""
    with st.spinner("🔄 Sincronizando tests de campo..."):
        success, records = gs.sync_field_data(sheet_url, trainer, worksheet)
        
        if success:
            if records:
                # Cargar datos existentes
                existing_data = load_json_data('field_tests.json', {'tests': []})
                
                # Agregar nuevos registros
                existing_data['tests'].extend(records)
                
                # Guardar
                with open('field_tests.json', 'w') as f:
                    json.dump(existing_data, f, indent=2)
                
                st.success(f"✅ {len(records)} tests de campo sincronizados correctamente!")
                
                # Mostrar resumen
                with st.expander("📊 Resumen de sincronización"):
                    df_summary = pd.DataFrame(records)
                    st.dataframe(df_summary[['player_name', 'test_type', 'result', 'unit']])
                
                # Guardar configuración
                config = load_sync_config()
                config['field_sheets'].append({
                    'url': sheet_url,
                    'trainer': trainer,
                    'worksheet': worksheet,
                    'last_sync': datetime.now().isoformat()
                })
                save_sync_config(config)
                
                st.balloons()
            else:
                st.warning("⚠️ No se encontraron datos para sincronizar")
        else:
            st.error(f"❌ Error en sincronización: {records}")

def connection_status(gs):
    """Mostrar estado de las conexiones"""
    st.subheader("📊 Estado de Conexiones")
    
    config = load_sync_config()
    
    # Conexiones médicas
    if config.get('medical_sheets'):
        st.write("### 🏥 Conexiones Médicas")
        for i, sheet in enumerate(config['medical_sheets']):
            with st.expander(f"Dr. {sheet['doctor']} - {sheet.get('last_sync', 'No sincronizado')[:10]}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**URL:** {sheet['url'][:50]}...")
                    st.write(f"**Hoja:** {sheet.get('worksheet', 'N/A')}")
                
                with col2:
                    # Test de conexión
                    if st.button(f"🔍 Probar", key=f"test_med_{i}"):
                        success, message = gs.test_connection(sheet['url'])
                        if success:
                            st.success("✅ OK")
                        else:
                            st.error("❌ Error")
                
                with col3:
                    # Re-sincronizar
                    if st.button(f"🔄 Sync", key=f"resync_med_{i}"):
                        sync_medical_data(gs, sheet['url'], sheet['doctor'], sheet.get('worksheet'))
    
    # Conexiones nutricionales
    if config.get('nutrition_sheets'):
        st.write("### 🥗 Conexiones Nutricionales")
        for i, sheet in enumerate(config['nutrition_sheets']):
            with st.expander(f"{sheet['nutritionist']} - {sheet.get('last_sync', 'No sincronizado')[:10]}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**URL:** {sheet['url'][:50]}...")
                    st.write(f"**Hoja:** {sheet.get('worksheet', 'N/A')}")
                
                with col2:
                    if st.button(f"🔍 Probar", key=f"test_nut_{i}"):
                        success, message = gs.test_connection(sheet['url'])
                        if success:
                            st.success("✅ OK")
                        else:
                            st.error("❌ Error")
                
                with col3:
                    if st.button(f"🔄 Sync", key=f"resync_nut_{i}"):
                        sync_nutrition_data(gs, sheet['url'], sheet['nutritionist'], sheet.get('worksheet'))
    
    # Conexiones de tests de fuerza
    if config.get('strength_sheets'):
        st.write("### 💪 Conexiones Tests de Fuerza")
        for i, sheet in enumerate(config['strength_sheets']):
            with st.expander(f"{sheet['trainer']} - {sheet.get('last_sync', 'No sincronizado')[:10]}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**URL:** {sheet['url'][:50]}...")
                    st.write(f"**Hoja:** {sheet.get('worksheet', 'N/A')}")
                
                with col2:
                    if st.button(f"🔍 Probar", key=f"test_str_{i}"):
                        success, message = gs.test_connection(sheet['url'])
                        if success:
                            st.success("✅ OK")
                        else:
                            st.error("❌ Error")
                
                with col3:
                    if st.button(f"🔄 Sync", key=f"resync_str_{i}"):
                        sync_strength_data(gs, sheet['url'], sheet['trainer'], sheet.get('worksheet'))
    
    # Conexiones de tests de campo
    if config.get('field_sheets'):
        st.write("### 🏃 Conexiones Tests de Campo")
        for i, sheet in enumerate(config['field_sheets']):
            with st.expander(f"{sheet['trainer']} - {sheet.get('last_sync', 'No sincronizado')[:10]}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**URL:** {sheet['url'][:50]}...")
                    st.write(f"**Hoja:** {sheet.get('worksheet', 'N/A')}")
                
                with col2:
                    if st.button(f"🔍 Probar", key=f"test_field_{i}"):
                        success, message = gs.test_connection(sheet['url'])
                        if success:
                            st.success("✅ OK")
                        else:
                            st.error("❌ Error")
                
                with col3:
                    if st.button(f"🔄 Sync", key=f"resync_field_{i}"):
                        sync_field_data(gs, sheet['url'], sheet['trainer'], sheet.get('worksheet'))

def sync_configuration(gs):
    """Configuración de sincronización"""
    st.subheader("⚙️ Configuración de Sincronización")
    
    # Sincronización automática
    auto_sync = st.checkbox("🔄 Sincronización automática", value=False)
    
    if auto_sync:
        sync_interval = st.selectbox(
            "⏰ Intervalo de sincronización:",
            ["Cada hora", "Cada 6 horas", "Diario", "Semanal"]
        )
        
        st.info(f"⏰ Sincronización configurada: {sync_interval}")
    
    # Configuración de mapeo de columnas
    with st.expander("🗂️ Mapeo de Columnas Personalizado"):
        st.write("**Configurar nombres de columnas en tus hojas:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Área Médica:**")
            st.text_input("Columna 'Jugador':", value="jugador")
            st.text_input("Columna 'Lesión':", value="lesion")
            st.text_input("Columna 'Severidad':", value="severidad")
        
        with col2:
            st.write("**Área Nutrición:**")
            st.text_input("Columna 'Jugador':", value="jugador", key="nut_player")
            st.text_input("Columna 'Plan':", value="plan")
            st.text_input("Columna 'Calorías':", value="calorias")
    
    # Plantillas de ejemplo
    with st.expander("📄 Plantillas de Google Sheets"):
        st.write("**Estructura recomendada para hojas médicas:**")
        st.code("""
Columnas requeridas:
- jugador (Nombre del jugador)
- division (División/Categoría)
- lesion (Tipo de lesión)
- severidad (Leve/Moderada/Grave)
- fecha (Fecha de la lesión)
- estado (En tratamiento/Recuperado)
- observaciones (Notas adicionales)
        """)
        
        st.write("**Estructura recomendada para hojas nutricionales:**")
        st.code("""
Columnas requeridas:
- jugador (Nombre del jugador)
- division (División/Categoría)
- plan (Tipo de plan nutricional)
- calorias (Calorías objetivo)
- proteinas (Gramos de proteína)
- carbohidratos (Gramos de carbohidratos)
- grasas (Gramos de grasa)
- observaciones (Notas adicionales)
        """)
    
    # Limpiar configuración
    if st.button("🗑️ Limpiar todas las conexiones"):
        save_sync_config({"medical_sheets": [], "nutrition_sheets": []})
        st.success("✅ Configuración limpiada")
        st.rerun()