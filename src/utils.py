import json
import os

def load_json_data(filename, default_data=None):
    """Carga un archivo JSON desde la carpeta data."""
    filepath = os.path.join('data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default_data if default_data is not None else {}