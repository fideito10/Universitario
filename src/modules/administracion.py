import streamlit as st
import pandas as pd
import gspread
import json
import os
from datetime import datetime, date
from google.oauth2 import service_account

def get_gcp_credentials():
    """Obtener credenciales desde service_account.json SIN MENSAJES DEBUG"""
    try:
        # Ruta al archivo real de credenciales
        credentials_path = 'credentials/service_account.json'
        
        if os.path.exists(credentials_path):
            with open(credentials_path, 'r') as f:
                credentials_info = json.load(f)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=[
                        "https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"
                    ]
                )
                return credentials
        else:
            st.error(f"❌ No se encontró el archivo de credenciales: {credentials_path}")
            st.info("💡 Asegúrese de que el archivo service_account.json esté en la carpeta credentials/")
            return None
            
    except json.JSONDecodeError:
        st.error("❌ El archivo service_account.json no es un JSON válido")
        return None
    except Exception as e:
        st.error(f"❌ Error cargando credenciales: {e}")
        return None

class JugadoresMaestroManager:
    def __init__(self):
        self.credentials = get_gcp_credentials()
        self.sheet_id = "1Lb-ngyjQQH-CFrrLJMvaVrknTWoGliEyr1-tZAFtQuw"
        self.worksheet_name = "Jugadores_Maestro"
        
        self.divisiones = [
            "Primera", "Reserva", "Juveniles M19", "Juveniles M17", 
            "Juveniles M15", "Infantiles M13", "Infantiles M11"
        ]
        
        self.posiciones = [
            "Pilar", "Hooker", "Segunda Línea", "Tercera Línea", 
            "Medio Scrum", "Apertura", "Centro", "Wing", "Fullback"
        ]
        
    def connect_to_sheet(self):
        """Conectar a Google Sheets de forma silenciosa"""
        try:
            if not self.credentials:
                return None
                
            gc = gspread.authorize(self.credentials)
            
            try:
                spreadsheet = gc.open_by_key(self.sheet_id)
            except gspread.SpreadsheetNotFound:
                st.error(f"❌ No se encontró el Google Sheets con ID: {self.sheet_id}")
                st.info("💡 Verifica que hayas compartido el Google Sheet con la cuenta de servicio")
                return None
            
            try:
                worksheet = spreadsheet.worksheet(self.worksheet_name)
            except gspread.WorksheetNotFound:
                # Fallback: Intentar obtener la primera hoja (gid=0)
                try:
                    worksheet = spreadsheet.get_worksheet(0)
                except Exception:
                    st.warning(f"⚠️ Hoja '{self.worksheet_name}' no existe. Creándola...")
                    worksheet = self.create_master_sheet(spreadsheet)
                
            return worksheet
            
        except Exception as e:
            st.error(f"❌ Error conectando a Google Sheets: {e}")
            return None
    
    def create_master_sheet(self, spreadsheet):
        """Crear hoja maestra si no existe"""
        try:
            worksheet = spreadsheet.add_worksheet(
                title=self.worksheet_name, 
                rows=1000, 
                cols=10
            )
            
            headers = [
                "DNI", "Nombre", "Apellido", "Posicion", 
                "Categoria", "Fecha_Nacimiento", "Fecha_Alta", 
                "Estado", "Email", "Telefono"
            ]
            worksheet.append_row(headers)
            
            worksheet.format('A1:J1', {
                'backgroundColor': {'red': 0.1, 'green': 0.17, 'blue': 0.34},
                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
            })
            
            st.success("✅ Hoja maestra creada exitosamente")
            return worksheet
            
        except Exception as e:
            st.error(f"❌ Error creando hoja maestra: {e}")
            return None
    
    def get_all_players(self):
        """Obtener todos los jugadores de la hoja maestra"""
        worksheet = self.connect_to_sheet()
        if not worksheet:
            return pd.DataFrame()
            
        try:
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"❌ Error obteniendo jugadores: {e}")
            return pd.DataFrame()
    
    def dni_exists(self, dni):
        """Verificar si un DNI ya existe"""
        df = self.get_all_players()
        if df.empty:
            return False
        return str(dni) in df['DNI'].astype(str).values
    
    def add_player(self, player_data):
        """Agregar nuevo jugador limpio y silencioso"""
        worksheet = self.connect_to_sheet()
        if not worksheet:
            st.error("❌ No se pudo conectar a Google Sheets")
            return False
        
        try:
            if self.dni_exists(player_data['dni']):
                st.error(f"❌ El DNI {player_data['dni']} ya existe")
                return False
            
            row_data = [
                str(player_data['dni']),
                player_data['nombre'],
                player_data['apellido'],
                player_data['posicion'],
                player_data['categoria'],
                player_data['fecha_nacimiento'].strftime('%d/%m/%Y'),
                datetime.now().strftime('%d/%m/%Y'),
                'Activo',
                player_data.get('email', ''),
                player_data.get('telefono', '')
            ]
            
            worksheet.append_row(row_data)
            st.success(f"✅ Jugador {player_data['nombre']} {player_data['apellido']} agregado exitosamente")
            st.cache_data.clear()
            return True
            
        except Exception as e:
            st.error(f"❌ Error agregando jugador: {e}")
            return False
    
    def update_player_status(self, dni, new_status):
        """Actualizar estado de un jugador"""
        worksheet = self.connect_to_sheet()
        if not worksheet:
            return False
            
        try:
            dni_column = worksheet.col_values(1)
            
            for i, cell_dni in enumerate(dni_column[1:], 2):
                if str(cell_dni) == str(dni):
                    worksheet.update_cell(i, 8, new_status)
                    st.success(f"✅ Estado actualizado para DNI: {dni}")
                    return True
            
            st.error(f"❌ No se encontró jugador con DNI: {dni}")
            return False
            
        except Exception as e:
            st.error(f"❌ Error actualizando estado: {e}")
            return False

def main_administracion():
    st.markdown("""
    <div class="main-header">
        <h1>👥 Administración - Universitario</h1>
        <h3>Gestión de Jugadores Base Maestra</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # ✅ FIX: Agregar key único al botón del sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("📋 Pasar Lista", use_container_width=True, key="btn_pasar_lista_sidebar"):
        st.session_state.show_lista = True
    
    if st.session_state.get('show_lista', False):
        from src.modules.Lista import main_lista
        main_lista()
        # ✅ FIX: Agregar key único al botón de volver
        if st.button("⬅️ Volver a Administración", key="btn_volver_admin"):
            st.session_state.show_lista = False
            st.rerun()
        return
    
    manager = JugadoresMaestroManager()
    
    tab1, tab2, tab3 = st.tabs(["➕ Agregar Jugador", "👥 Ver Jugadores", "⚙️ Gestión"])
    
    with tab1:
        st.subheader("➕ Agregar Nuevo Jugador")
        
        if 'form_key' not in st.session_state:
            st.session_state.form_key = 0
        
        # ✅ FIX: El form ya tiene key único con form_key
        with st.form(f"add_player_form_{st.session_state.form_key}"):
            col1, col2 = st.columns(2)
            
            with col1:
                dni = st.text_input("🆔 DNI *", placeholder="12345678")
                nombre = st.text_input("👤 Nombre *", placeholder="Juan")
                apellido = st.text_input("👤 Apellido *", placeholder="Pérez")
                email = st.text_input("📧 Email", placeholder="juan.perez@ejemplo.com")
            
            with col2:
                posicion = st.selectbox("🏉 Posición *", manager.posiciones)
                categoria = st.selectbox("🏆 Categoría *", manager.divisiones)
                fecha_nacimiento = st.date_input("📅 Fecha de Nacimiento *", 
                                            min_value=date(1990, 1, 1),
                                            max_value=date.today())
                telefono = st.text_input("📱 Teléfono", placeholder="+54 9 11 1234-5678")
            
            submitted = st.form_submit_button("✅ Agregar Jugador", use_container_width=True)
            
            if submitted:
                if not all([dni, nombre, apellido]):
                    st.error("❌ Complete todos los campos obligatorios (*)")
                elif len(str(dni)) < 7:
                    st.error("❌ DNI debe tener al menos 7 dígitos")
                else:
                    player_data = {
                        'dni': dni,
                        'nombre': nombre.title(),
                        'apellido': apellido.title(),
                        'posicion': posicion,
                        'categoria': categoria,
                        'fecha_nacimiento': fecha_nacimiento,
                        'email': email.lower(),
                        'telefono': telefono
                    }
                    
                    if manager.add_player(player_data):
                        st.balloons()
                        st.session_state.form_key += 1
                        st.success("🎉 ¡Formulario listo para el siguiente jugador!")
                        st.rerun()
    
    with tab2:
        st.subheader("👥 Base de Jugadores")
        
        df_players = manager.get_all_players()
        
        if not df_players.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_categoria = st.selectbox("Filtrar por Categoría", 
                                              ["Todas"] + df_players['Categoria'].unique().tolist(),
                                              key="select_categoria_filter")
            with col2:
                filter_posicion = st.selectbox("Filtrar por Posición", 
                                             ["Todas"] + df_players['Posicion'].unique().tolist(),
                                             key="select_posicion_filter")
            with col3:
                filter_estado = st.selectbox("Filtrar por Estado", 
                                           ["Todos"] + df_players['Estado'].unique().tolist(),
                                           key="select_estado_filter")
            
            filtered_df = df_players.copy()
            if filter_categoria != "Todas":
                filtered_df = filtered_df[filtered_df['Categoria'] == filter_categoria]
            if filter_posicion != "Todas":
                filtered_df = filtered_df[filtered_df['Posicion'] == filter_posicion]
            if filter_estado != "Todos":
                filtered_df = filtered_df[filtered_df['Estado'] == filter_estado]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Jugadores", len(filtered_df))
            with col2:
                activos = len(filtered_df[filtered_df['Estado'] == 'Activo'])
                st.metric("Activos", activos)
            with col3:
                primera = len(filtered_df[filtered_df['Categoria'] == 'Primera'])
                st.metric("Primera División", primera)
            with col4:
                juveniles = len(filtered_df[filtered_df['Categoria'].str.contains('Juveniles', na=False)])
                st.metric("Juveniles", juveniles)
            
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )
            
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"jugadores_car_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="btn_download_csv"  # ✅ FIX: Agregar key único
            )
        else:
            st.info("ℹ️ No hay jugadores registrados aún")
    
    with tab3:
        st.subheader("⚙️ Gestión del Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔄 Cambiar Estado de Jugador")
            df_players = manager.get_all_players()
            
            if not df_players.empty:
                selected_dni = st.selectbox(
                    "Seleccionar jugador (DNI - Nombre)",
                    options=df_players['DNI'].tolist(),
                    format_func=lambda x: f"{x} - {df_players[df_players['DNI']==x]['Nombre'].iloc[0]} {df_players[df_players['DNI']==x]['Apellido'].iloc[0]}",
                    key="select_dni_status"  # ✅ FIX: Agregar key único
                )
                
                new_status = st.selectbox("Nuevo Estado", 
                                        ["Activo", "Inactivo", "Lesionado", "Suspendido"],
                                        key="select_new_status")  # ✅ FIX: Agregar key único
                
                if st.button("🔄 Actualizar Estado", key="btn_update_status"):  # ✅ FIX: Agregar key único
                    manager.update_player_status(selected_dni, new_status)
        
        with col2:
            st.markdown("#### 📊 Estadísticas")
            if not df_players.empty:
                st.write("**Por Categoría:**")
                categoria_counts = df_players['Categoria'].value_counts()
                st.bar_chart(categoria_counts)

if __name__ == "__main__":
    main_administracion()