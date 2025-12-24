"""
Script para mostrar el contenido de secrets.toml
que debes copiar a Streamlit Cloud
"""

from pathlib import Path

def show_secrets():
    """Mostrar contenido de secrets.toml para copiar"""
    
    secrets_file = Path(__file__).parent / '.streamlit' / 'secrets.toml'
    
    if not secrets_file.exists():
        print("[X] Error: No se encontro el archivo .streamlit/secrets.toml")
        print("[!] Ejecuta primero: python setup_secrets.py")
        return
    
    print("=" * 70)
    print("CONTENIDO PARA COPIAR A STREAMLIT CLOUD")
    print("=" * 70)
    print("\n[!] Instrucciones:")
    print("1. Selecciona y copia TODO el texto de abajo")
    print("2. Ve a https://share.streamlit.io")
    print("3. Abre tu app > Settings > Secrets")
    print("4. Pega el contenido completo")
    print("5. Haz clic en 'Save'\n")
    print("=" * 70)
    print("INICIO DEL CONTENIDO")
    print("=" * 70)
    
    with open(secrets_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
    
    print("=" * 70)
    print("FIN DEL CONTENIDO")
    print("=" * 70)
    print(f"\n[OK] Total de caracteres: {len(content)}")
    print("[!] Asegurate de copiar TODO, incluyendo [google] y las comillas")

if __name__ == "__main__":
    show_secrets()
