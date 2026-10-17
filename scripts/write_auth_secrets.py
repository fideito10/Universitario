"""Arma la seccion [auth] de .streamlit/secrets.toml desde variables de entorno (Railway).

Streamlit lee la config de st.login solo desde secrets.toml, y en Railway los secretos son variables.
Se ejecuta antes de `streamlit run` (ver Procfile). No hace nada si faltan variables o si el archivo
ya tiene [auth] (por ejemplo en desarrollo local). Nunca imprime valores.
"""
import hashlib
import os
from pathlib import Path

ARCHIVO = Path(".streamlit") / "secrets.toml"


def main() -> int:
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    base = os.environ.get("SESSION_SECRET", "").strip()
    if not (client_id and client_secret and base):
        return 0
    if ARCHIVO.exists() and "[auth]" in ARCHIVO.read_text(encoding="utf-8"):
        return 0
    redirect = os.environ.get("OAUTH_REDIRECT_URI", "").strip()
    if not redirect:
        dominio = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
        if not dominio:
            print("write_auth_secrets: falta OAUTH_REDIRECT_URI o RAILWAY_PUBLIC_DOMAIN; Google desactivado")
            return 0
        redirect = f"https://{dominio}/oauth2callback"
    cookie_secret = hashlib.sha256(("auth:" + base).encode()).hexdigest()
    bloque = (
        "\n[auth]\n"
        f'redirect_uri = "{redirect}"\n'
        f'cookie_secret = "{cookie_secret}"\n'
        f'client_id = "{client_id}"\n'
        f'client_secret = "{client_secret}"\n'
        'server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"\n'
    )
    ARCHIVO.parent.mkdir(exist_ok=True)
    with ARCHIVO.open("a", encoding="utf-8") as f:
        f.write(bloque)
    print("write_auth_secrets: [auth] de Google configurado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
