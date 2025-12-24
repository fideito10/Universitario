# 🔐 Configuración de Credenciales para Google Sheets

Este documento explica cómo configurar las credenciales de Google Cloud para que funcionen tanto en desarrollo local como en Streamlit Cloud.

## 📋 Para Streamlit Cloud (Producción)

### 1. Ir a la configuración de tu app
1. Ve a https://share.streamlit.io/
2. Busca tu aplicación "clubargentinorugby" 
3. Haz clic en **"Settings"** (⚙️)
4. Selecciona **"Secrets"**

### 2. Agregar las credenciales como secrets
Copia y pega el siguiente formato en el editor de secrets, reemplazando con tus valores reales del archivo `service_account.json`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "tu-project-id"
private_key_id = "tu-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\ntu-private-key-completa\n-----END PRIVATE KEY-----\n"
client_email = "tu-service-account@tu-project.iam.gserviceaccount.com"
client_id = "tu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/service/v1/metadata/x509/tu-service-account%40tu-project.iam.gserviceaccount.com"
```

### 3. Guardar la configuración
- Haz clic en **"Save"**
- La aplicación se redesplegará automáticamente

## 🏠 Para Desarrollo Local

### Opción 1: Usar archivo local (actual)
- Mantén tu archivo `credentials/service_account.json`
- El código detectará automáticamente si está en local o cloud

### Opción 2: Usar secrets localmente
1. Crea un archivo `.streamlit/secrets.toml` en la raíz del proyecto
2. Copia el contenido del ejemplo anterior
3. Reemplaza con tus credenciales reales

## 🔄 Cómo Funciona el Sistema

El código actualizado funciona de la siguiente manera:

1. **Primero** intenta leer desde `st.secrets["gcp_service_account"]` (Streamlit Cloud)
2. **Si falla**, busca archivos locales en estas ubicaciones:
   - `credentials/service_account.json`
   - `../credentials/service_account.json`
   - `C:/Users/dell/Desktop/Car/credentials/service_account.json`

## ⚠️ Seguridad

- ✅ **Nunca subas** archivos de credenciales a GitHub
- ✅ Los secrets en Streamlit Cloud están **encriptados**
- ✅ El archivo `.gitignore` está configurado para excluir credenciales
- ✅ Usa diferentes service accounts para desarrollo y producción

## 🆘 Troubleshooting

Si tienes problemas:

1. **Verifica que las credenciales estén bien formateadas** (especialmente la private_key)
2. **Asegúrate que el service account tenga permisos** en las hojas de Google Sheets
3. **Comprueba que las APIs estén habilitadas** (Google Sheets API y Google Drive API)
4. **Revisa los logs** en Streamlit Cloud para errores específicos