"""
Script para configurar secrets.toml desde service_account.json
Ejecutar: python setup_secrets.py
"""

import json
import os
from pathlib import Path

def setup_streamlit_secrets():
    """Configurar archivo secrets.toml desde service_account.json"""
    
    # Rutas
    project_root = Path(__file__).parent
    credentials_file = project_root / 'credentials' / 'service_account.json'
    streamlit_dir = project_root / '.streamlit'
    secrets_file = streamlit_dir / 'secrets.toml'
    
    print("[*] Configurando Streamlit Secrets...")
    print(f"[>] Proyecto: {project_root}")
    
    # Verificar que existe el archivo de credenciales
    if not credentials_file.exists():
        print(f"[X] Error: No se encontro {credentials_file}")
        print("[!] Asegurate de tener el archivo service_account.json en la carpeta credentials/")
        return False
    
    # Crear directorio .streamlit si no existe
    streamlit_dir.mkdir(exist_ok=True)
    print(f"[OK] Directorio .streamlit creado/verificado")
    
    # Leer credenciales JSON
    try:
        with open(credentials_file, 'r', encoding='utf-8') as f:
            creds = json.load(f)
        print(f"[OK] Credenciales leidas desde {credentials_file.name}")
    except Exception as e:
        print(f"[X] Error leyendo credenciales: {e}")
        return False
    
    # Crear contenido TOML
    toml_content = "[google]\n"
    
    # Mapear campos JSON a TOML
    for key, value in creds.items():
        if isinstance(value, str):
            # Escapar comillas y saltos de línea en el private_key
            if key == "private_key":
                # Usar triple comillas para strings multilínea
                toml_content += f'{key} = """{value}"""\n'
            else:
                # Escapar comillas dobles
                escaped_value = value.replace('"', '\\"')
                toml_content += f'{key} = "{escaped_value}"\n'
        else:
            toml_content += f'{key} = {json.dumps(value)}\n'
    
    # Escribir archivo secrets.toml
    try:
        with open(secrets_file, 'w', encoding='utf-8') as f:
            f.write(toml_content)
        print(f"[OK] Archivo secrets.toml creado exitosamente")
        print(f"[>] Ubicacion: {secrets_file}")
        
        # Mostrar primeras líneas para verificar
        print("\n[>] Primeras lineas del archivo:")
        lines = toml_content.split('\n')[:5]
        for line in lines:
            if line and not 'private' in line.lower():
                print(f"   {line}")
        
        print("\n[OK] Configuracion completada!")
        print("\n[!] IMPORTANTE para Streamlit Cloud:")
        print("   1. Ve a tu app en https://share.streamlit.io")
        print("   2. Haz clic en 'Settings' > 'Secrets'")
        print("   3. Copia el contenido de .streamlit/secrets.toml")
        print("   4. Pegalo en el editor de secrets de Streamlit Cloud")
        print("   5. Haz clic en 'Save'")
        
        return True
        
    except Exception as e:
        print(f"[X] Error escribiendo secrets.toml: {e}")
        return False

if __name__ == "__main__":
    success = setup_streamlit_secrets()
    if success:
        print("\n[OK] Listo! Ahora puedes ejecutar tu app de Streamlit")
    else:
        print("\n[X] Hubo un error en la configuracion")
