# 🏥 Área Médica Mejorada - Club Argentino de Rugby

## 📋 Resumen del Sistema

El sistema ha sido completamente renovado para utilizar **Google Sheets como base de datos principal**, eliminando la dependencia de archivos locales y permitiendo colaboración en tiempo real entre profesionales médicos.

## 🎯 Funcionalidades Implementadas

### ✅ **Conexión Segura con Google Sheets**
- ✅ Soporte para `st.secrets` (recomendado para producción)
- ✅ Fallback a archivos de credenciales locales
- ✅ Validación automática de permisos y conexión
- ✅ Manejo robusto de errores de autenticación

### ✅ **Gestión Completa de Datos Médicos**
- ✅ `load_data_from_sheets()` - Cargar datos desde Google Sheets
- ✅ `add_new_record()` - Agregar nuevos registros médicos
- ✅ `update_record()` - Actualizar registros existentes
- ✅ `delete_record()` - Eliminar registros (funcionalidad adicional)
- ✅ Validación automática de datos

### ✅ **Interfaz Mejorada**
- ✅ Dashboard con métricas en tiempo real
- ✅ Filtros avanzados (División, Estado, Severidad, Texto libre)
- ✅ Visualización de registros con código de colores por severidad
- ✅ Formulario completo con validaciones
- ✅ Análisis estadísticos con gráficos interactivos

### ✅ **Modo Dual de Operación**
- ✅ **Google Sheets (Recomendado)**: Colaboración en tiempo real
- ✅ **Sistema Local (Respaldo)**: Funcionamiento sin conexión
- ✅ Cambio dinámico entre modos desde la interfaz

## 🔧 Configuración del Sistema

### 1. **Configuración con st.secrets (Recomendado)**

Crear archivo `.streamlit/secrets.toml`:

```toml
[google_sheets]
type = "service_account"
project_id = "tu-proyecto-google-cloud"
private_key_id = "tu-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nTU_PRIVATE_KEY_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "tu-service-account@tu-proyecto.iam.gserviceaccount.com"
client_id = "tu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
sheet_id = "1zGyW-M_VV7iyDKVB1TTd0EEP3QBjdoiBmSJN2tK-H7w"
```

### 2. **Configuración con Archivo Local (Alternativa)**

Mantener el archivo `car_google_credentials.json` en la raíz del proyecto.

## 🚀 Cómo Iniciar el Sistema

### **Opción 1: Inicio Rápido**
```bash
cd "c:\Users\dell\Desktop\Car"
streamlit run main_app.py
```

La aplicación estará disponible en:
- **Local**: http://localhost:8501
- **Red**: http://192.168.0.46:8501

### **Opción 2: Configuración Completa**

1. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

2. **Configurar credenciales de Google Sheets**:
   - Opción A: Usar `st.secrets` (ver configuración arriba)
   - Opción B: Colocar `car_google_credentials.json` en la raíz

3. **Ejecutar aplicación**:
```bash
streamlit run main_app.py
```

## 📊 Estructura de Datos

### **Hoja de Google Sheets: "Registros_Medicos"**

| Campo | Descripción | Tipo |
|-------|-------------|------|
| `ID` | Identificador único | Numérico |
| `Timestamp` | Fecha y hora de creación | DateTime |
| `Nombre_Profesional` | Nombre del médico | Texto |
| `Email_Profesional` | Email del médico | Email |
| `Nombre_Paciente` | Nombre del jugador | Texto |
| `Division` | División del jugador | Lista |
| `Diagnostico` | Diagnóstico médico | Texto |
| `Fecha_Atencion` | Fecha de la consulta | Fecha |
| `Tipo_Lesion` | Tipo de lesión | Lista |
| `Severidad` | Nivel de severidad | Lista |
| `Parte_Cuerpo` | Zona afectada | Lista |
| `Tratamiento` | Tratamiento prescrito | Texto |
| `Tiempo_Recuperacion` | Tiempo estimado | Texto |
| `Puede_Entrenar` | Estado para entrenamiento | Lista |
| `Medicamentos` | Medicación prescrita | Texto |
| `Observaciones` | Notas adicionales | Texto |
| `Proxima_Evaluacion` | Fecha de seguimiento | Fecha |
| `Estado` | Estado actual del caso | Auto-calculado |
| `Fecha_Registro` | Fecha de registro | Auto-generado |

## 🎯 Nuevas Funcionalidades

### **Dashboard Médico**
- 📊 **Métricas en tiempo real**: Total registros, casos del día, profesionales activos, casos graves
- 📈 **Indicadores visuales**: Cards con código de colores según criticidad
- 🔄 **Actualización automática**: Datos sincronizados con Google Sheets

### **Formulario Mejorado**
- ✅ **Validaciones en tiempo real**
- 📋 **Campos categorizados**: Información del profesional, paciente, diagnóstico, tratamiento
- 🎯 **Listas desplegables inteligentes**: Opciones predefinidas para consistencia
- 💾 **Guardado inmediato**: Confirmación visual del registro

### **Visualización Avanzada**
- 🔍 **Filtros múltiples**: Por profesional, división, severidad, estado, texto libre
- 🎨 **Código de colores**: Verde (leve), Amarillo (moderada), Rojo (grave)
- 📊 **Tabla interactiva**: Ordenamiento y paginación automática
- 📥 **Exportación**: Descarga en formato CSV

### **Análisis Estadísticos**
- 📈 **Gráficos interactivos**: Distribución por división, severidad, tipos de lesión
- 📅 **Análisis temporal**: Evolución de lesiones por mes
- 👨‍⚕️ **Ranking de profesionales**: Profesionales más activos
- 📊 **Métricas calculadas**: Porcentajes, tendencias, promedios

### **Panel de Administración**
- 🔧 **Diagnóstico del sistema**: Test de conexión, estado de credenciales
- 🔄 **Sincronización**: Backup local/Google Sheets
- 📥 **Exportación masiva**: Todos los registros en CSV
- ⚙️ **Configuración dinámica**: Cambio de modo de operación

## 🛠️ Solución de Problemas

### **Error: "Credenciales no cargadas"**
1. Verificar que existe `.streamlit/secrets.toml` con las credenciales correctas
2. O verificar que existe `car_google_credentials.json` en la raíz
3. Comprobar permisos del Service Account en Google Cloud

### **Error: "Hoja de trabajo no encontrada"**
1. El sistema crea automáticamente la hoja "Registros_Medicos"
2. Verificar que el `sheet_id` en las credenciales es correcto
3. Asegurar que el Service Account tiene acceso de escritura al spreadsheet

### **Error: "Conexión fallida"**
1. Verificar conexión a internet
2. Comprobar que el spreadsheet existe y es accesible
3. Validar credenciales en Google Cloud Console

### **Cambiar entre Modos**
- **Google Sheets → Local**: Los datos se mantienen en Google Sheets, pero la app funciona en modo local
- **Local → Google Sheets**: Cambio automático, sincronización disponible en administración

## 📚 Arquitectura del Sistema

```
src/
├── modules/
│   ├── areamedica_enhanced.py      # Sistema médico mejorado
│   └── auth_manager.py             # Sistema de autenticación
├── sheets/
│   ├── google_sheets_manager.py    # Manager Google Sheets mejorado
│   └── formularios_google_sheets.py # Compatibilidad con sistema anterior
└── utils.py                        # Utilidades del sistema

.streamlit/
└── secrets.toml                    # Credenciales seguras (recomendado)

car_google_credentials.json         # Credenciales alternativas
```

## 🎯 Próximas Mejoras

- [ ] **Notificaciones automáticas**: Alertas por email para casos graves
- [ ] **Integración con calendario**: Recordatorios de citas de seguimiento
- [ ] **Reportes automáticos**: PDFs con estadísticas mensuales
- [ ] **API REST**: Acceso programático para otras aplicaciones
- [ ] **Backup automático**: Respaldo programado de datos críticos

## 📞 Soporte

Para problemas técnicos o consultas sobre el sistema:

1. **Verificar logs**: Panel de Administración → Ver Información de Conexión
2. **Modo de emergencia**: Cambiar a "Sistema Local" si hay problemas con Google Sheets
3. **Documentación**: Revisar este archivo y archivos de ejemplo
4. **Contacto técnico**: Información disponible en el panel de administración

---

### 🏉 **Club Argentino de Rugby - Sistema Digital de Gestión Médica**
*Sistema desarrollado para optimizar la gestión de lesiones deportivas y mejorar la atención médica de los jugadores.*