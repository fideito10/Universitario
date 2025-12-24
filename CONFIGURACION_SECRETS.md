# Guía de Configuración de Credenciales para Streamlit Cloud

## Problema Resuelto
✅ El código ahora maneja correctamente las credenciales tanto localmente como en Streamlit Cloud.

## Cambios Realizados

### 1. Archivo Local: `.streamlit/secrets.toml`
- ✅ Ya se creó automáticamente con el script `setup_secrets.py`
- ✅ Contiene las credenciales de Google Cloud desde `service_account.json`
- ✅ Está en `.gitignore` (no se sube a GitHub por seguridad)

### 2. Código Actualizado: `formularios_google_sheets.py`
- ✅ Intenta primero cargar desde `st.secrets["google"]` (Streamlit Cloud)
- ✅ Si falla, usa el archivo local `credentials/service_account.json`
- ✅ Agrega `self.client` como alias de `self.gc` para compatibilidad

## Configuración en Streamlit Cloud

### Paso 1: Copiar el contenido de secrets.toml
Abre el archivo `.streamlit/secrets.toml` que se creó localmente y copia TODO su contenido.

### Paso 2: Configurar en Streamlit Cloud
1. Ve a tu aplicación en: https://share.streamlit.io
2. Busca tu app "Universitario" o "clubuniversitario"
3. Haz clic en el menú de tres puntos (⋮) de tu app
4. Selecciona **"Settings"**
5. En el menú lateral, haz clic en **"Secrets"**
6. Pega el contenido completo de `.streamlit/secrets.toml`
7. Haz clic en **"Save"**
8. Reinicia la aplicación (puede reiniciarse automáticamente)

### Paso 3: Verificar
Una vez configurado, la aplicación debería:
- ✅ Conectarse a Google Sheets correctamente
- ✅ Cargar la Base Central de Universitario
- ✅ Mostrar datos de todos los módulos
- ✅ No mostrar errores de credenciales

## Formato del archivo secrets.toml

El archivo debe verse así:

```toml
[google]
type = "service_account"
project_id = "tu-proyecto-id"
private_key_id = "..."
private_key = """-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
"""
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

## Solución de Problemas

### Error: "No se encontró el archivo de credenciales"
- **Localmente**: Verifica que existe `.streamlit/secrets.toml`
- **En Cloud**: Configura los secrets en la interfaz web de Streamlit

### Error: "No se pudieron cargar datos de los módulos"
- Verifica que los secrets estén correctamente configurados en Streamlit Cloud
- Asegúrate de que la cuenta de servicio tenga permisos en las hojas de Google

### Error: "La Base Central está vacía"
- Verifica que el Google Sheet esté compartido con el email de la cuenta de servicio
- El email está en el campo `client_email` de tus credenciales

## Comandos Útiles

### Recrear secrets.toml localmente
```bash
python setup_secrets.py
```

### Verificar que el archivo existe
```bash
dir .streamlit\secrets.toml
```

## Seguridad

⚠️ **IMPORTANTE**:
- ✅ `.streamlit/secrets.toml` está en `.gitignore`
- ✅ `credentials/service_account.json` está en `.gitignore`
- ❌ NUNCA subas estos archivos a GitHub
- ✅ Solo configura secrets en la interfaz web de Streamlit Cloud

## Próximos Pasos

1. ✅ Código actualizado y subido a GitHub
2. ⏳ Configurar secrets en Streamlit Cloud (manual)
3. ⏳ Verificar que la app funcione correctamente

---

**Fecha**: 2025-12-24
**Commit**: 6b38de2
