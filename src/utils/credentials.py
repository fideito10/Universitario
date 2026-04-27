"""
Módulo centralizado de credenciales para el proyecto Universitario.
Soporta: st.secrets (local), Variables de Entorno (Railway/Docker), archivo local.
"""

import os
import json
import streamlit as st
from google.oauth2 import service_account

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials_dict() -> dict | None:
    """
    Obtiene el diccionario de credenciales desde la fuente disponible.
    Orden de prioridad: st.secrets → Variables de Entorno → archivo local.
    Retorna un dict con los campos de service account, o None si falla.
    """

    # 1. Intentar desde st.secrets (Streamlit Cloud / local .streamlit/secrets.toml)
    try:
        secrets = st.secrets  # Esto lanza error si no existe el archivo
        for section in ["google", "google_sheets", "gcp_service_account"]:
            if section in secrets:
                data = secrets[section]
                creds = {
                    k: (data[k] if isinstance(data, dict) else getattr(data, k))
                    for k in data
                }
                if "type" in creds and "private_key" in creds:
                    if creds.get("private_key"):
                        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
                    return creds
    except Exception:
        pass  # No hay secrets.toml → continuar

    # 2. Intentar desde Variables de Entorno (Railway, Docker, etc.)
    prefix = None
    if os.getenv("STREAMLIT_GOOGLE_TYPE"):
        prefix = "STREAMLIT_GOOGLE_"
    elif os.getenv("GOOGLE_TYPE"):
        prefix = "GOOGLE_"

    if prefix:
        private_key = os.getenv(f"{prefix}PRIVATE_KEY", "")
        # Railway puede almacenar \n literales — normalizarlos
        private_key = private_key.replace("\\n", "\n")

        creds = {
            "type": os.getenv(f"{prefix}TYPE", "service_account"),
            "project_id": os.getenv(f"{prefix}PROJECT_ID", ""),
            "private_key_id": os.getenv(f"{prefix}PRIVATE_KEY_ID", ""),
            "private_key": private_key,
            "client_email": os.getenv(f"{prefix}CLIENT_EMAIL", ""),
            "client_id": os.getenv(f"{prefix}CLIENT_ID", ""),
            "auth_uri": os.getenv(f"{prefix}AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv(f"{prefix}TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "",
        }
        if creds["client_email"] and creds["private_key"]:
            return creds

    # 3. Intentar desde archivo local (desarrollo)
    possible_paths = [
        "credentials/service_account.json",
        "credentials/service-account-key.json",
        "credentials/google_credentials.json",
        "car_google_credentials.json",
        "google_credentials.json",
        "service_account.json",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

    return None  # No se encontraron credenciales


def get_service_account_credentials(scopes=None):
    """
    Retorna un objeto google.oauth2.service_account.Credentials listo para usar.
    Retorna None si no se pueden obtener credenciales.
    """
    if scopes is None:
        scopes = SCOPES

    creds_dict = get_credentials_dict()
    if creds_dict is None:
        return None

    try:
        return service_account.Credentials.from_service_account_info(
            creds_dict, scopes=scopes
        )
    except Exception:
        return None
