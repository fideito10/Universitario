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
    """Módulo de perfil personalizado adaptativo según el rol"""
    cargar_estilos_profesionales()
    
    # Obtener el usuario actual
    user = st.session_state.get('user', {})
    user_dni = user.get('dni', '')
    user_nombre = user.get('nombre', 'Usuario')
    user_rol = user.get('rol', 'Invitado')
    
    # Header dinámico
    header_label = "MI PERFIL DEPORTIVO" if user_rol == "Jugador" else f"PERFIL PROFESIONAL"
    sub_label = "Mis métricas y evolución" if user_rol == "Jugador" else f"Gestión de {user_rol}"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #000000 0%, #212529 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
        text-align: center;
        border: 2px solid rgba(255,255,255,0.1);
    ">
        <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 800; letter-spacing: 1px;">{header_label}</h1>
        <p style="color: #E0E0E0; margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9; font-weight: 300;">
            {user_nombre} · {user_rol} · Universitario 2026
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Si es Jugador, seguimos la lógica estándar
    if user_rol == "Jugador":
        if not user_dni:
            st.error("❌ No se encontró un DNI asociado a tu cuenta. Contacta al administrador.")
            return

        with st.spinner("🔄 Cargando tu información..."):
            df_combinado = crear_dataframe_integrado()
        
        if df_combinado.empty:
            st.error("❌ No se pudieron cargar datos del sistema.")
            return

        col_dni = buscar_columna_dni(df_combinado)
        if not col_dni:
            st.error("No se pudo identificar la estructura de datos para DNI.")
            return

        df_combinado[col_dni] = df_combinado[col_dni].apply(normalizar_dni)
        dni_busqueda = normalizar_dni(user_dni)
        player_row = df_combinado[df_combinado[col_dni] == dni_busqueda]
        
        if player_row.empty:
            st.warning(f"⚠️ Hola {user_nombre}, aún no tenemos registros vinculados a tu DNI ({user_dni}).")
            st.info("💡 Asegúrate de que tu DNI esté correctamente cargado en la Base Maestra.")
            return

        col_nombre = 'Nombre y Apellido' if 'Nombre y Apellido' in df_combinado.columns else (
                     'Nombre completo del jugador' if 'Nombre completo del jugador' in df_combinado.columns else 
                     df_combinado.columns[0])
        
        nombre_jugador_full = player_row.iloc[0][col_nombre]
        jugador_formato_360 = f"{nombre_jugador_full} (DNI: {user_dni})"
        datos_jugador = obtener_datos_jugador(df_combinado, jugador_formato_360)
        
        mostrar_ficha_personal_simple(datos_jugador)
        st.divider()
        crear_panel_areas_unificado(datos_jugador)
    
    else:
        # Vista para Admin / Entrenador / Staff
        st.markdown("### 📋 Datos de Miembro del Staff")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div style="background:white; padding:1.5rem; border-radius:15px; box-shadow:0 4px 12px rgba(0,0,0,0.05); text-align:center;">
                <div style="font-size:2rem;">👤</div>
                <div style="font-weight:700; color:#111; margin-top:0.5rem;">{user_nombre}</div>
                <div style="font-size:0.8rem; color:#666;">Nombre Completo</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background:white; padding:1.5rem; border-radius:15px; box-shadow:0 4px 12px rgba(0,0,0,0.05); text-align:center;">
                <div style="font-size:2rem;">🛡️</div>
                <div style="font-weight:700; color:#111; margin-top:0.5rem;">{user_rol}</div>
                <div style="font-size:0.8rem; color:#666;">Rol en el Sistema</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div style="background:white; padding:1.5rem; border-radius:15px; box-shadow:0 4px 12px rgba(0,0,0,0.05); text-align:center;">
                <div style="font-size:2rem;">🆔</div>
                <div style="font-weight:700; color:#111; margin-top:0.5rem;">{user_dni if user_dni else "No asignado"}</div>
                <div style="font-size:0.8rem; color:#666;">Documento de Identidad</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Acciones rápidas según el rol
        st.markdown("### ⚡ Acciones Rápidas")
        
        if user_rol == "Administrador":
            # Para Admin, mostramos herramientas de gestión
            cols = st.columns(3)
            with cols[0]:
                if st.button("👥 Gestión Jugadores", use_container_width=True):
                    st.session_state.current_page = "administracion"
                    st.rerun()
            with cols[1]:
                if st.button("🧠 Asistente IA", use_container_width=True):
                    st.session_state.current_page = "bot"
                    st.rerun()
            with cols[2]:
                if st.button("📊 Panel 360°", use_container_width=True):
                    st.session_state.current_page = "dashboard_360"
                    st.rerun()
        
        elif user_rol in ["Entrenador", "Preparador Físico", "Nutricionista"]:
            # Para Staff técnico
            cols = st.columns(3)
            with cols[0]:
                if st.button("📊 Ir a Dashboard 360°", use_container_width=True):
                    st.session_state.current_page = "dashboard_360"
                    st.rerun()
            with cols[1]:
                page_lista = "lista" if user_rol != "Nutricionista" else "nutricion"
                label_lista = "📋 Lista Asistencia" if user_rol != "Nutricionista" else "🥗 Planes Nutri"
                if st.button(label_lista, use_container_width=True):
                    st.session_state.current_page = page_lista
                    st.rerun()
            with cols[2]:
                page_area = "fisica" if user_rol != "Nutricionista" else "wellness"
                label_area = "🏋️ Área Física" if user_rol != "Nutricionista" else "📝 Bienestar"
                if st.button(label_area, use_container_width=True):
                    st.session_state.current_page = page_area
                    st.rerun()
        
        st.info(f"💡 Como {user_rol}, tienes acceso completo a todos los módulos habilitados según tus permisos de seguridad.")

    # Pie de página común
    st.markdown("---")
    st.markdown("""
    <div style="background: rgba(0,0,0,0.03); border-radius: 15px; padding: 1rem; text-align: center;">
        <p style="color: #888; margin: 0; font-size: 0.85rem;">Club Universitario de La Plata · Sistema Conectado Online</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main_perfil_jugador()
