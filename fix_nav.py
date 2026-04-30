"""
Reemplaza el bloque MOBILE BOTTOM NAV con enfoque de hidden text input.
"""
with open('main_universitario.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar el bloque a reemplazar
start_marker = '    # ===== MOBILE BOTTOM NAV ====='
end_marker = '    # ===== ROUTING ====='

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f"MARKERS NOT FOUND: start={start_idx}, end={end_idx}")
    exit(1)

new_block = '''    # ===== MOBILE BOTTOM NAV =====
    # Construir items segun permisos
    nav_items = [("\\U0001f3e0", "Inicio", "dashboard")]
    if auth_manager.has_permission("perfil"):
        nav_items.append(("\\U0001f464", "Perfil", "perfil"))
    if auth_manager.has_permission("fisica"):
        nav_items.append(("\\U0001f3cb", "Fisica", "fisica"))
    if auth_manager.has_permission("medica"):
        nav_items.append(("\\U0001f3e5", "Medica", "medica"))
    if auth_manager.has_permission("nutricion"):
        nav_items.append(("\\U0001f957", "Nutricion", "nutricion"))
    if auth_manager.has_permission("wellness"):
        nav_items.append(("\\U0001f4dd", "Wellness", "wellness"))
    nav_items = nav_items[:5]

    # ── Input oculto como canal JS → Streamlit ──
    # El JS del bottom nav setea este input, Streamlit lo detecta y navega
    st.markdown("""
        <style>
        div[data-testid="stTextInput"]:has(input[placeholder="__NAVTRIGGER__"]) {
            position: fixed !important;
            top: -9999px !important;
            left: -9999px !important;
            width: 1px !important;
            height: 1px !important;
            overflow: hidden !important;
            opacity: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    nav_trigger = st.text_input(
        "nav",
        value="",
        key="__nav_trigger__",
        placeholder="__NAVTRIGGER__",
        label_visibility="collapsed"
    )
    if nav_trigger and auth_manager.has_permission(nav_trigger):
        st.session_state.current_page = nav_trigger
        st.session_state["__nav_trigger__"] = ""
        st.rerun()

    # ── Bottom bar HTML ── onclick setea el input via JS nativo de React
    current_page = st.session_state.get("current_page", "dashboard")
    nav_links_html = ""
    for icon, label, page_id in nav_items:
        active_class = "active" if current_page == page_id else ""
        js = (
            f"event.preventDefault();"
            f"(function(){{"
            f"  var inp=document.querySelector('input[placeholder=\\"__NAVTRIGGER__\\"]');"
            f"  if(inp){{"
            f"    var setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"
            f"    setter.call(inp,'{page_id}');"
            f"    inp.dispatchEvent(new Event('input',{{bubbles:true}}));"
            f"  }}"
            f"}})();"
        )
        # Mostrar label con acento correcto para UI
        display_labels = {
            "Inicio": "Inicio", "Perfil": "Perfil", "Fisica": "F\\u00edsica",
            "Medica": "M\\u00e9dica", "Nutricion": "Nutrici\\u00f3n", "Wellness": "Wellness"
        }
        display = display_labels.get(label, label)
        nav_links_html += (
            f\'<a href="#" onclick="{js}" class="mbn-item {active_class}">\'
            f\'<span class="mbn-icon">{icon}</span>\'
            f\'<span class="mbn-label">{display}</span>\'
            f\'</a>\'
        )

    st.markdown(f"""
        <style>
        .mobile-bottom-nav {{ display: none !important; }}
        @media (max-width: 768px) {{
            .mobile-bottom-nav {{
                display: flex !important;
                flex-direction: row !important;
                position: fixed !important;
                bottom: 0 !important; left: 0 !important; right: 0 !important;
                width: 100% !important;
                z-index: 999999 !important;
                background: #0d0d0d !important;
                border-top: 1px solid rgba(255,255,255,0.12) !important;
                box-shadow: 0 -4px 20px rgba(0,0,0,0.5) !important;
                padding: 6px 0 10px !important;
                margin: 0 !important;
                justify-content: space-around !important;
                align-items: center !important;
            }}
            .mbn-item {{
                flex: 1 !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 3px !important;
                padding: 4px 2px !important;
                color: rgba(255,255,255,0.45) !important;
                text-decoration: none !important;
                -webkit-tap-highlight-color: transparent !important;
                cursor: pointer !important;
            }}
            .mbn-item.active {{ color: #4fc3f7 !important; }}
            .mbn-item:active   {{ color: #ffffff !important; }}
            .mbn-icon {{ font-size: 1.35rem !important; line-height: 1 !important; }}
            .mbn-label {{
                font-size: 0.58rem !important;
                font-weight: 500 !important;
                letter-spacing: 0.04em !important;
                text-transform: uppercase !important;
            }}
            .mbn-item.active .mbn-label {{ font-weight: 700 !important; }}
            section.main > div.block-container {{ padding-bottom: 90px !important; }}
        }}
        </style>
        <div class="mobile-bottom-nav">{nav_links_html}</div>
    """, unsafe_allow_html=True)

    '''

content = content[:start_idx] + new_block + content[end_idx:]

with open('main_universitario.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS")
