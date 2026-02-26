import streamlit as st
import pandas as pd
from datetime import datetime
from src.modules.dashboard_360 import (
    crear_dataframe_integrado, 
    obtener_datos_jugador, 
    mostrar_ficha_personal_simple,
    crear_panel_areas_unificado,
    cargar_estilos_profesionales,
    buscar_columna_dni,
    normalizar_dni
)

def main_perfil_jugador():
    """Módulo de perfil personalizado para el jugador logueado"""
    cargar_estilos_profesionales()
    
    # Obtener el usuario actual
    user = st.session_state.get('user', {})
    user_dni = user.get('dni', '')
    user_nombre = user.get('nombre', 'Jugador')
    
    if not user_dni:
        st.error("❌ No se encontró un DNI asociado a tu cuenta. Contacta al administrador.")
        return

    # Header de Perfil Personal
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #000000 0%, #212529 100%);
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
        text-align: center;
        border: 2px solid rgba(255,255,255,0.1);
    ">
        <h1 style="color: white; margin: 0; font-size: 2.8rem; font-weight: 800; letter-spacing: 1px;">MI PERFIL DEPORTIVO</h1>
        <p style="color: #E0E0E0; margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9; font-weight: 300;">
            Club Universitario de La Plata - Temporada 2026
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Obtener datos integrados
    with st.spinner("🔄 Cargando tu información..."):
        df_combinado = crear_dataframe_integrado()
    
    if df_combinado.empty:
        st.error("❌ No se pudieron cargar datos del sistema.")
        return

    # Buscar al jugador específicamente por su DNI
    col_dni = buscar_columna_dni(df_combinado)
    if not col_dni:
        st.error("No se pudo identificar la estructura de datos para DNI.")
        return

    # Normalizar para búsqueda robusta (DNI limpio de puntos, espacios, etc.)
    df_combinado[col_dni] = df_combinado[col_dni].apply(normalizar_dni)
    dni_busqueda = normalizar_dni(user_dni)
    
    player_row = df_combinado[df_combinado[col_dni] == dni_busqueda]
    
    if player_row.empty:
        st.warning(f"⚠️ Hola {user_nombre}, aún no tenemos registros vinculados a tu DNI ({user_dni}) en las bases de datos del club.")
        st.info("💡 Asegúrate de que tu DNI esté correctamente cargado en la Base Maestra por el administrador.")
        
        # Mostrar datos básicos de la sesión al menos
        st.markdown("### Mis Datos de Acceso")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Nombre:** {user_nombre}")
        with col2:
            st.info(f"**DNI:** {user_dni}")
        return

    # Si hay datos, mostrar el panel unificado (igual que el 360 pero directo)
    # Primero obtenemos el formato de nombre que usa el 360 para filtrar
    col_nombre = 'Nombre y Apellido' if 'Nombre y Apellido' in df_combinado.columns else (
                 'Nombre completo del jugador' if 'Nombre completo del jugador' in df_combinado.columns else 
                 df_combinado.columns[0])
    
    nombre_jugador_full = player_row.iloc[0][col_nombre]
    jugador_formato_360 = f"{nombre_jugador_full} (DNI: {user_dni})"
    
    # Obtener todos los registros del jugador
    datos_jugador = obtener_datos_jugador(df_combinado, jugador_formato_360)
    
    # Mostrar la ficha
    mostrar_ficha_personal_simple(datos_jugador)
    
    st.divider()
    
    # Mostrar el panel de las 3 áreas
    crear_panel_areas_unificado(datos_jugador)
    
    # Sección de evolución o mensajes
    st.markdown("---")
    st.markdown("""
    <div style="background: rgba(0,0,0,0.03); border-radius: 15px; padding: 1.5rem; text-align: center;">
        <h4 style="margin: 0; color: #2C2C2C;">🎯 Seguimiento de Objetivos</h4>
        <p style="color: #666; margin-top: 0.5rem;">Cualquier discrepancia en tus datos, por favor consulta con tu preparador físico o el área médica.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main_perfil_jugador()
