"""Check-in por QR: pantalla del jugador (abre el link del QR) y panel del staff."""
from __future__ import annotations

import io
import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.data import backend, repo_checkin

COOKIE = "uni_dev"
COOKIE_DIAS = 365
MAX_INTENTOS = 5  # vinculaciones fallidas por sesion


def _leer_cookie() -> str:
    try:
        return st.context.cookies.get(COOKIE, "") or ""
    except Exception:
        return ""


def _guardar_cookie(token: str) -> None:
    """Guarda/renueva el token en el celu (JS en un iframe del mismo origen).

    Safari borra las cookies escritas por JS a los 7 dias: por eso se renueva en cada escaneo.
    """
    t = json.dumps(token)
    components.html(
        f"""<script>
        (function() {{
          var c = "{COOKIE}=" + {t} + "; max-age={COOKIE_DIAS * 86400}; path=/; SameSite=Lax" +
                  (location.protocol === "https:" ? "; Secure" : "");
          try {{ window.parent.document.cookie = c; }} catch (e) {{ document.cookie = c; }}
        }})();
        </script>""", height=0)


def _etiqueta_dispositivo() -> str:
    try:
        return (st.context.headers.get("User-Agent", "") or "")[:200]
    except Exception:
        return ""


def _url_por_defecto() -> str:
    """APP_URL si está definida; si no, la dirección desde la que se abrió la app."""
    fija = backend._setting("APP_URL")
    if fija:
        return fija
    try:
        h = st.context.headers
        host = h.get("X-Forwarded-Host") or h.get("Host") or ""
        if not host:
            return ""
        proto = h.get("X-Forwarded-Proto") or (
            "http" if host.startswith(("localhost", "127.", "192.168.", "10.")) else "https")
        return f"{proto}://{host}"
    except Exception:
        return ""


def _estilos() -> None:
    st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stToolbar"], [data-testid="stHeader"],
    footer, #MainMenu { display: none !important; }
    .main .block-container { max-width: 480px; padding-top: 2rem; }
    .chk-ok { background:#e8f5e9; border:2px solid #2e7d32; border-radius:16px;
              padding:1.5rem 1rem; text-align:center; color:#1b5e20; }
    .chk-ok h1 { margin:0; font-size:2.2rem; }
    .chk-ok p { margin:.3rem 0 0; font-size:1.1rem; }
    </style>""", unsafe_allow_html=True)


def _exito(jug: dict, resultado: str) -> None:
    hora = repo_checkin.ahora().strftime("%H:%M")
    titulo = "✅ Presente" if resultado == "nuevo" else "✅ Ya estabas presente"
    st.markdown(
        f"""<div class="chk-ok"><h1>{titulo}</h1>
        <p><b>{jug['nombre']} {jug['apellido']}</b></p>
        <p>{jug['categoria']} · {hora} hs</p></div>""", unsafe_allow_html=True)


def pantalla_checkin() -> None:
    """Destino del QR (?checkin=1). No requiere login: identifica por celu vinculado."""
    _estilos()
    st.markdown("### 🏉 Universitario · Asistencia")

    if not backend.use_postgres():
        st.error("El check-in por QR requiere DATA_BACKEND=postgres.")
        return

    # 1) Celu ya vinculado: presente directo.
    token = _leer_cookie()
    if token:
        try:
            dni = repo_checkin.dni_de_token(token)
            if dni:
                resultado, jug = repo_checkin.registrar_presente(dni)
                if jug:
                    _guardar_cookie(token)  # renueva la vigencia
                    backend.limpiar_cache()
                    _exito(jug, resultado)
                    return
        except Exception as e:
            st.error(f"No se pudo registrar la asistencia ({type(e).__name__}). Probá de nuevo.")
            return

    # 2) Primera vez en este celu: vincular con DNI + fecha de nacimiento.
    st.info("Primera vez en este celular: ingresá tus datos una sola vez. "
            "Después alcanza con escanear el QR.")
    intentos = st.session_state.get("chk_intentos", 0)
    if intentos >= MAX_INTENTOS:
        st.error("Demasiados intentos. Pedile al staff que te vincule el celular.")
        return

    with st.form("chk_vincular"):
        dni = st.text_input("DNI (sin puntos)", inputmode="numeric")
        nac = st.text_input("Fecha de nacimiento (dd/mm/aaaa)", placeholder="dd/mm/aaaa")
        enviar = st.form_submit_button("Marcar presente", type="primary",
                                       use_container_width=True)
    if not enviar:
        return

    try:
        jug = repo_checkin.verificar_jugador(dni, nac)
        if jug is None:
            st.session_state["chk_intentos"] = intentos + 1
            st.error("Los datos no coinciden. Revisá el DNI y la fecha de nacimiento. "
                     "Si el problema sigue, avisale al staff.")
            return
        token = repo_checkin.vincular_dispositivo(jug["dni"], _etiqueta_dispositivo())
    except repo_checkin.LimiteDispositivos:
        st.error(f"Ya tenés {repo_checkin.MAX_DISPOSITIVOS} celulares vinculados. "
                 "Pedile al staff que los reinicie.")
        return
    except Exception as e:
        st.error(f"No se pudo vincular el celular ({type(e).__name__}). Probá de nuevo.")
        return

    try:
        resultado, jug = repo_checkin.registrar_presente(jug["dni"])
    except Exception as e:
        st.error(f"Celular vinculado, pero no se pudo registrar el presente "
                 f"({type(e).__name__}). Volvé a escanear el QR.")
        _guardar_cookie(token)
        return
    _guardar_cookie(token)
    backend.limpiar_cache()
    st.session_state["chk_intentos"] = 0
    _exito(jug, resultado)


# --------------------------------------------------------------------------- staff
def _qr_png(url: str) -> bytes:
    import qrcode
    img = qrcode.make(url, box_size=12, border=3)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def panel_qr_asistencia() -> None:
    """Tab del panel de Gestion Jugadores: QR, presentes de hoy y reinicio de celulares."""
    if not backend.use_postgres():
        st.warning("El check-in por QR requiere DATA_BACKEND=postgres.")
        return

    st.subheader("📱 QR de asistencia")
    st.caption("Un QR permanente: pegalo en el vestuario o la cancha. Cada jugador lo escanea "
               "con la cámara del celular.")
    base = st.text_input("URL pública de la app", value=_url_por_defecto(),
                         placeholder="https://tu-app.up.railway.app",
                         help="Se completa con la dirección actual. Para fijarla, usá la "
                              "variable APP_URL.")
    if base.strip():
        if any(h in base for h in ("localhost", "127.0.0.1")):
            st.warning("Con 'localhost' el QR solo funciona en esta PC. Para probar con el "
                       "celular usá la IP de la red (ej. http://192.168.0.52:8501) o la URL "
                       "pública de la app.")
        url = base.strip().rstrip("/") + "/?checkin=1"
        png = _qr_png(url)
        c1, c2 = st.columns([1, 1])
        with c1:
            st.image(png, caption=url, use_container_width=True)
        with c2:
            st.download_button("⬇️ Descargar QR (PNG)", png, "qr_asistencia.png", "image/png",
                               use_container_width=True)
    else:
        st.info("Ingresá la URL de la app para generar el QR.")

    st.divider()
    st.subheader("✅ Presentes hoy")
    try:
        pres = repo_checkin.presentes_hoy()
    except Exception as e:
        st.error(f"No se pudo leer la asistencia ({type(e).__name__}).")
        pres = []
    st.metric("Presentes", len(pres))
    if pres:
        st.dataframe(pd.DataFrame(pres), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🔄 Reiniciar celulares de un jugador")
    st.caption("Si el jugador cambió de celular, desvinculá los anteriores; "
               "vuelve a vincular con DNI + fecha de nacimiento.")
    dni = st.text_input("DNI del jugador", key="chk_reset_dni", inputmode="numeric")
    if dni.strip():
        try:
            disp = repo_checkin.dispositivos_de(dni)
        except Exception as e:
            st.error(f"No se pudo leer ({type(e).__name__}).")
            return
        if not disp:
            st.info("Ese DNI no tiene celulares vinculados.")
        else:
            st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)
            if st.button("Desvincular todos", key="chk_reset_btn"):
                n = repo_checkin.revocar_dispositivos(dni)
                st.success(f"{n} celular(es) desvinculado(s).")
                st.rerun()
