import toml
import os

def generate_railway_env():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if not os.path.exists(secrets_path):
        print(f"Error: No se encontró {secrets_path}")
        return

    with open(secrets_path, "r", encoding="utf-8") as f:
        config = toml.load(f)

    print("# --- COPIA Y PEGA ESTO EN RAILWAY (Variables de Entorno) ---\n")
    
    # Manejar sección [google]
    if "google" in config:
        for key, value in config["google"].items():
            env_key = f"STREAMLIT_GOOGLE_{key.upper()}"
            # Para la clave privada, asegurarnos de que las nuevas líneas se manejen bien
            if key == "private_key":
                print(f'{env_key}="{value}"')
            else:
                print(f'{env_key}={value}')

    # Manejar sección [google_sheets]
    if "google_sheets" in config:
        for key, value in config["google_sheets"].items():
            env_key = f"STREAMLIT_GOOGLE_SHEETS_{key.upper()}"
            if key == "private_key":
                print(f'{env_key}="{value}"')
            else:
                print(f'{env_key}={value}')

    # Manejar gemini_api_key
    if "gemini_api_key" in config:
        print(f'STREAMLIT_GEMINI_API_KEY={config["gemini_api_key"]}')
    
    # Puerto de Railway
    print("\n# Configuración de Streamlit para Railway")
    print("STREAMLIT_SERVER_PORT=${{PORT}}")
    print("STREAMLIT_SERVER_ADDRESS=0.0.0.0")

if __name__ == "__main__":
    generate_railway_env()
