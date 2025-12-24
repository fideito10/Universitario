# 🏥 Sistema de Formularios Médicos - CAR Rugby Club

## 📋 Descripción del Sistema

Sistema completo de captura, almacenamiento y visualización de datos médicos utilizando:
- **Frontend**: Streamlit con autenticación segura
- **Base de Datos**: Google Sheets API
- **Backend**: Python con gspread y pandas
- **Seguridad**: Autenticación por roles y credenciales Google Cloud

## 🚀 Características Principales

### ✅ Formulario de Captura Médica
- **Información del Profesional**: Nombre, email (auto-completado desde autenticación)
- **Datos del Paciente**: Nombre, división, fecha de atención
- **Diagnóstico**: Tipo de lesión, severidad, parte del cuerpo afectada
- **Tratamiento**: Recomendaciones, tiempo de recuperación, medicamentos
- **Seguimiento**: Próxima evaluación, observaciones adicionales

### ✅ Autenticación Segura
- **Sistema de Login**: Usuario y contraseña hasheada
- **Control de Roles**: Médico, Nutricionista, Administrador
- **Gestión de Sesiones**: Timeout automático de 8 horas
- **Logs de Acceso**: Registro de todos los ingresos

### ✅ Integración Google Sheets
- **Escritura Automática**: Envío directo con `sheet.append_row()`
- **Lectura en Tiempo Real**: Visualización inmediata de datos
- **Sincronización**: Integración con sistema CAR existente
- **Backup Automático**: Datos seguros en la nube

### ✅ Analytics y Visualización
- **Métricas en Tiempo Real**: Total registros, casos graves, profesionales activos
- **Gráficos Interactivos**: Distribución por división, severidad, tipos de lesión
- **Filtros Dinámicos**: Por profesional, división, severidad
- **Exportación**: Descarga de datos en CSV

## 🔧 Instalación y Configuración

### Paso 1: Dependencias
```bash
pip install streamlit gspread google-auth google-auth-oauthlib pandas plotly
```

### Paso 2: Credenciales Google Cloud
1. **Crear Proyecto** en Google Cloud Console
2. **Habilitar APIs**: Google Sheets API, Google Drive API
3. **Crear Service Account** con permisos de Editor
4. **Descargar JSON** de credenciales
5. **Renombrar archivo** a `car_google_credentials.json`
6. **Colocar en carpeta raíz** del proyecto

### Paso 3: Configurar Google Sheet
1. **Compartir Google Sheet** con email de service account
2. **Permisos**: Editor
3. **Copiar Sheet ID** de la URL
4. **Actualizar configuración** en `formularios_google_sheets.py`

### Paso 4: Estructura de Archivos
```
Car/
├── main_app.py                           # Aplicación principal
├── car_google_credentials.json           # Credenciales Google (NO subir a Git)
├── src/
│   ├── modules/
│   │   ├── auth_manager.py              # Sistema de autenticación
│   │   └── formularios_medicos_interface.py  # Interfaz completa
│   └── sheets/
│       └── formularios_google_sheets.py  # Manager Google Sheets
└── data/
    └── medical_users.json               # Usuarios del sistema
```

## 🔐 Configuración de Seguridad

### Variables de Entorno (Producción)
```bash
# En lugar de usar archivo JSON, usar variables de entorno:
export GOOGLE_CREDENTIALS='{"type": "service_account", ...}'
export GOOGLE_SHEET_ID="1zGyW-M_VV7iyDKVB1TTd0EEP3QBjdoiBmSJN2tK-H7w"
```

### Usuarios por Defecto
```
Médico:
- Usuario: dr.garcia
- Contraseña: medico123

Nutricionista:
- Usuario: dra.lopez  
- Contraseña: nutricion123

Administrador:
- Usuario: admin.car
- Contraseña: admin123
```

## 🚀 Despliegue en Producción

### Opción 1: Google Cloud Run
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/car-medical-system', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/car-medical-system']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'car-medical', '--image', 'gcr.io/$PROJECT_ID/car-medical-system', '--region', 'us-central1']
```

### Opción 2: Servidor Privado (VPS)
```bash
# Instalar dependencias
sudo apt update
sudo apt install python3-pip nginx

# Clonar proyecto
git clone <repositorio>
cd car-medical-system

# Instalar dependencias Python
pip3 install -r requirements.txt

# Configurar Nginx
sudo nano /etc/nginx/sites-available/car-medical

# Ejecutar con systemd
sudo systemctl enable car-medical.service
sudo systemctl start car-medical.service
```

### Opción 3: Render
```yaml
# render.yaml
services:
  - type: web
    name: car-medical-system
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run main_app.py --server.port $PORT
    envVars:
      - key: GOOGLE_CREDENTIALS
        sync: false
      - key: GOOGLE_SHEET_ID
        sync: false
```

## 📊 Uso del Sistema

### Para Profesionales Médicos
1. **Acceder** a la aplicación web
2. **Iniciar sesión** con credenciales asignadas
3. **Ir a "Formularios Médicos"** en el menú
4. **Completar** el formulario con datos del paciente
5. **Enviar**: Los datos se guardan automáticamente en Google Sheets
6. **Visualizar** registros en tiempo real

### Para Administradores
1. **Acceso completo** a todos los registros
2. **Gestión de usuarios** y permisos
3. **Sincronización** con sistema CAR
4. **Visualización de logs** de acceso
5. **Analytics avanzados** y exportación de datos

## 🔒 Consideraciones de Seguridad

### Datos Sensibles
- **NO usar Streamlit Community Cloud** (datos médicos sensibles)
- **Usar servidor privado** o Google Cloud Run
- **Configurar HTTPS** obligatorio
- **Backup automático** de datos críticos

### Credenciales
```python
# INCORRECTO - No hacer esto:
GOOGLE_CREDENTIALS = {"type": "service_account", ...}

# CORRECTO - Usar variables de entorno:
import os
credentials_json = os.getenv('GOOGLE_CREDENTIALS')
```

### Control de Acceso
- **Sesiones con timeout** (8 horas)
- **Contraseñas hasheadas** con salt
- **Logs de acceso** completos
- **Roles diferenciados** por funcionalidad

## 📈 Monitoreo y Mantenimiento

### Logs del Sistema
```python
# Ubicación de logs
data/medical_users.json  # Logs de acceso
Google Sheets            # Respaldo automático de formularios
```

### Métricas Importantes
- **Registros por día**
- **Profesionales activos**
- **Casos graves detectados**
- **Tiempo de respuesta del sistema**

### Backup y Recuperación
```bash
# Backup automático diario
0 2 * * * python3 /path/to/backup_script.py

# Backup de Google Sheets
gcloud auth activate-service-account --key-file=credentials.json
gsutil cp gs://backup-bucket/medical-data-$(date +%Y%m%d).csv ./
```

## 🆘 Solución de Problemas

### Error: "Credenciales no cargadas"
```bash
# Verificar archivo existe
ls -la car_google_credentials.json

# Verificar permisos
chmod 600 car_google_credentials.json

# Verificar formato JSON
python3 -m json.tool car_google_credentials.json
```

### Error: "No se puede escribir en Google Sheets"
1. **Verificar** que el Sheet esté compartido con la service account
2. **Confirmar permisos** de "Editor" 
3. **Probar** con Sheet ID correcto
4. **Verificar APIs** habilitadas en Google Cloud

### Error: "Módulo no encontrado"
```bash
# Verificar estructura de archivos
tree src/

# Reinstalar dependencias
pip3 install --upgrade -r requirements.txt

# Verificar paths en main_app.py
python3 -c "import sys; print(sys.path)"
```

## 📞 Soporte

### Contacto Técnico
- **Email**: desarrollo@carrugby.com
- **Documentación**: [Enlace a docs]
- **Issues**: [Enlace a GitHub Issues]

### Recursos Adicionales
- **Google Sheets API**: https://developers.google.com/sheets/api
- **Streamlit Docs**: https://docs.streamlit.io
- **gspread Library**: https://docs.gspread.org

---

## 🎯 Notas de Desarrollo

### Próximas Funcionalidades
- [ ] Notificaciones automáticas por email
- [ ] Integración con calendario para citas
- [ ] Reportes PDF automatizados
- [ ] API REST para integraciones externas
- [ ] Dashboard móvil responsivo

### Versioning
- **v1.0**: Sistema base con formularios y autenticación
- **v1.1**: Analytics avanzados y exportación
- **v1.2**: Integración completa con sistema CAR
- **v2.0**: API REST y dashboard móvil (planificado)

**¡Sistema listo para producción con datos médicos sensibles!** 🏥🚀