# 🏉 Sistema de Gestión - Club Argentino de Rugby (CAR)

## 📋 Descripción

Sistema integral de digitalización desarrollado en **Streamlit** para el Club Argentino de Rugby, enfocado en la gestión del **Área Médica** y **Área Nutrición**. El sistema permite un control completo de lesiones, planes nutricionales y seguimiento de la salud deportiva de todos los jugadores del club.

## ✨ Características Principales

### 🏥 **Área Médica**
- **📊 Dashboard interactivo** con métricas en tiempo real
- **📋 Registro de lesiones** completo y detallado
- **🔍 Filtros avanzados** por división y estado
- **📈 Gráficos dinámicos** de análisis de lesiones
- **👨‍⚕️ Seguimiento médico** con asignación de doctores
- **📅 Control de fechas** de lesión y recuperación estimada

### 🥗 **Área Nutrición**
- **📊 Planes nutricionales** personalizados por jugador
- **💊 Control de suplementación** con dosificación y frecuencia
- **🧮 Calculadora nutricional** avanzada con BMR y TDEE
- **📈 Análisis por división** de calorías y macronutrientes
- **🎯 Objetivos personalizados** según plan deportivo
- **👩‍⚕️ Asignación de nutricionistas**

### 🔐 **Sistema de Autenticación**
- **Login seguro** con encriptación SHA-256
- **Gestión de sesiones** persistentes
- **Roles de usuario** (admin/user)
- **Base de datos JSON** local para desarrollo

## 🚀 Instalación y Configuración

### **1. Clonar o Descargar el Proyecto**
```bash
cd c:\Users\dell\Desktop\Car
```

### **2. Instalar Dependencias**
```bash
pip install -r requirements.txt
```

### **3. Ejecutar la Aplicación**
```bash
streamlit run main_app.py
```

### **4. Acceder al Sistema**
- **URL Local:** http://localhost:8501
- **Usuario:** admin
- **Contraseña:** admin123

## 📁 Estructura del Proyecto

```
Car/
├── 📄 main_app.py              # Aplicación principal de Streamlit
├── 📄 club_data.py             # Configuración y datos del CAR
├── 📄 utils.py                 # Utilidades y funciones auxiliares
├── 📄 requirements.txt         # Dependencias de Python
├── 📁 .streamlit/
│   └── 📄 config.toml          # Configuración de Streamlit
├── 📄 users_credentials.json   # Base de datos de usuarios
├── 📄 medical_records.json     # Registros médicos (se crea automáticamente)
├── 📄 nutrition_records.json   # Registros nutricionales (se crea automáticamente)
├── 📄 car.jpg                  # Logo del club (opcional)
├── 📄 README.md               # Documentación principal
└── 📄 LOGO_GUIDE.md           # Guía para implementar el logo
```

## 🎨 Diseño y UI/UX

### **Colores Institucionales CAR**
- **Azul Oscuro:** #1A2C56 (Color principal)
- **Celeste:** #6BB4E8 (Color secundario)
- **Blanco:** #FFFFFF
- **Gris Claro:** #F5F5F5

### **Tipografía**
- **Fuente Principal:** Inter (Google Fonts)
- **Pesos:** 300, 400, 500, 600, 700

### **Elementos de Diseño**
- ✅ **Gradientes** azul oscuro a celeste
- ✅ **Tarjetas con sombras** y bordes redondeados
- ✅ **Métricas destacadas** con colores institucionales
- ✅ **Responsive design** para todas las pantallas
- ✅ **Animaciones suaves** en interacciones

## 🏥 Manual del Área Médica

### **Dashboard Médico**
1. **📊 Métricas Principales:**
   - Total de lesiones registradas
   - Lesiones en recuperación activa
   - Jugadores ya recuperados
   - Casos graves que requieren atención especial

2. **📈 Gráficos de Análisis:**
   - **Barras:** Lesiones por división
   - **Circular:** Distribución por severidad (Leve, Moderada, Grave)

3. **🔍 Filtros Avanzados:**
   - **Por División:** Primera, Reserva, Juveniles, Infantiles, Mini Rugby
   - **Por Estado:** En recuperación, Recuperado, Todos

### **Registro de Lesiones**
1. **👤 Datos del Jugador:**
   - Nombre completo
   - División a la que pertenece

2. **🩹 Información Médica:**
   - Tipo de lesión específica
   - Severidad (Leve/Moderada/Grave)
   - Fecha de ocurrencia
   - Fecha estimada de recuperación

3. **👨‍⚕️ Seguimiento:**
   - Médico tratante asignado
   - Observaciones y notas del tratamiento

### **Personal Médico Disponible**
- **Dr. García** - Medicina Deportiva
- **Dr. Fernández** - Traumatología
- **Lic. Kinesiólogo Martín** - Kinesiología Deportiva
- **Lic. Kinesiólogo Ana** - Rehabilitación

## 🥗 Manual del Área Nutrición

### **Dashboard Nutricional**
1. **📊 Métricas Principales:**
   - Planes nutricionales activos
   - Promedio de calorías por división
   - Suplementos en uso
   - Divisiones con seguimiento nutricional

2. **📈 Análisis Nutricional:**
   - **Calorías por División:** Comparativa de requerimientos
   - **Tipos de Planes:** Distribución de objetivos nutricionales

### **🧮 Calculadora Nutricional**
La calculadora permite calcular automáticamente:

1. **⚙️ Parámetros de Entrada:**
   - Peso del jugador (kg)
   - Altura (cm)
   - Edad
   - Nivel de actividad física
   - Objetivo deportivo

2. **📊 Cálculos Automáticos:**
   - **BMR:** Tasa Metabólica Basal (Harris-Benedict)
   - **Calorías Totales:** Ajustadas por actividad y objetivo
   - **Proteínas:** Específicas para deportistas (1.6-2.0g/kg)
   - **Carbohidratos:** Según tipo de deporte (4-6g/kg)
   - **Grasas:** 25% de calorías totales

### **Tipos de Planes Nutricionales**
- **🔄 Mantenimiento:** Para conservar peso y rendimiento
- **💪 Ganancia de masa muscular:** Superávit calórico controlado
- **📉 Definición:** Déficit calórico con alta proteína
- **📈 Crecimiento:** Para jugadores en desarrollo (juveniles)
- **🏥 Recuperación post-lesión:** Planes especializados
- **🏆 Pre-competencia:** Optimización para competición
- **🔋 Post-competencia:** Recuperación y reposición

### **💊 Control de Suplementación**
- **Registro detallado** de cada suplemento
- **Dosificación precisa** y frecuencia de uso
- **Fechas de inicio y fin** del tratamiento
- **Seguimiento personalizado** por jugador

### **Personal de Nutrición**
- **Lic. María López** - Nutrición Deportiva
- **Lic. Juan Nutricionista** - Nutrición Clínica
- **Dr. Deportólogo Pérez** - Medicina del Deporte

## 🔐 Gestión de Usuarios

### **Credenciales por Defecto**
- **Usuario Administrador:**
  - Usuario: `admin`
  - Contraseña: `admin123`
  - Permisos: Acceso completo al sistema

### **Archivo de Usuarios**
```json
{
  "admin": {
    "password": "hash_sha256",
    "name": "Administrador",
    "email": "admin@car.com.ar",
    "role": "admin",
    "created_at": "fecha_iso"
  }
}
```

### **Características de Seguridad**
- ✅ **Contraseñas encriptadas** con SHA-256
- ✅ **Validación de sesiones** persistente
- ✅ **Control de acceso** por roles
- ✅ **Timeouts de sesión** configurables

## 📊 Base de Datos y Persistencia

### **Archivos de Datos**
1. **📄 users_credentials.json** - Usuarios del sistema
2. **📄 medical_records.json** - Registros médicos y lesiones
3. **📄 nutrition_records.json** - Planes nutricionales y suplementos

### **Formato de Datos Médicos**
```json
{
  "injuries": [
    {
      "id": 1,
      "player_name": "Juan Pérez",
      "division": "Primera",
      "injury_type": "Esguince de tobillo",
      "severity": "Leve",
      "date_occurred": "2025-09-15",
      "expected_recovery": "2025-10-15",
      "status": "En recuperación",
      "doctor": "Dr. García",
      "notes": "Reposo y fisioterapia"
    }
  ]
}
```

### **Formato de Datos Nutricionales**
```json
{
  "meal_plans": [
    {
      "id": 1,
      "player_name": "Juan Pérez",
      "division": "Primera",
      "plan_type": "Ganancia de masa muscular",
      "calories_target": 3500,
      "protein_target": 150,
      "carbs_target": 400,
      "fat_target": 120,
      "created_date": "2025-09-01",
      "nutritionist": "Lic. María López",
      "notes": "Plan para aumento de peso controlado"
    }
  ],
  "supplements": [
    {
      "id": 1,
      "player_name": "Juan Pérez",
      "supplement": "Proteína Whey",
      "dosage": "30g post-entrenamiento",
      "frequency": "Diario",
      "start_date": "2025-09-01",
      "end_date": "2025-12-01"
    }
  ]
}
```

## 📈 Gráficos y Visualizaciones

### **Tecnología Utilizada**
- **Plotly Express** para gráficos interactivos
- **Pandas** para manipulación de datos
- **Streamlit** para la interfaz web

### **Tipos de Gráficos**
1. **📊 Gráficos de Barras:**
   - Lesiones por división
   - Calorías promedio por división

2. **🥧 Gráficos Circulares:**
   - Distribución por severidad de lesiones
   - Tipos de planes nutricionales

3. **📈 Métricas:**
   - Contadores en tiempo real
   - Indicadores de tendencia

## 🔧 Configuración Avanzada

### **Personalización de Colores**
Editar las variables en `club_data.py`:
```python
"colors": {
    "primary": "#1A2C56",    # Azul oscuro
    "secondary": "#6BB4E8",  # Celeste
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545"
}
```

### **Configuración de Streamlit**
Archivo `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#6BB4E8"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#1A2C56"
font = "sans serif"
```

### **Agregar Personal Médico/Nutricional**
Modificar en `club_data.py`:
```python
"medical_staff": [
    {
        "name": "Dr. Nuevo",
        "specialty": "Especialidad",
        "license": "MN XXXXX",
        "phone": "(011) 4XXX-XXXX",
        "email": "nuevo@car.com.ar"
    }
]
```

## 🚀 Funcionalidades Futuras

### **Próximas Implementaciones**
- [ ] **📧 Sistema de notificaciones** por email
- [ ] **📱 Aplicación móvil** responsive
- [ ] **🗄️ Base de datos externa** (PostgreSQL/MySQL)
- [ ] **📄 Generación de reportes** en PDF
- [ ] **📊 Dashboard ejecutivo** para directivos
- [ ] **🔔 Alertas automáticas** de seguimiento
- [ ] **📤 Exportación de datos** a Excel
- [ ] **🔐 Autenticación de dos factores** (2FA)
- [ ] **📋 Historial clínico** completo
- [ ] **🎯 Objetivos y metas** nutricionales

### **Integraciones Potenciales**
- [ ] **💳 Sistema de facturación** médica
- [ ] **📅 Calendar de citas** médicas
- [ ] **📞 Recordatorios** automáticos
- [ ] **📊 Analytics avanzados** con IA
- [ ] **🏥 Integración con sistemas** hospitalarios

## 🔧 Solución de Problemas

### **Problemas Comunes**

#### **Error: ModuleNotFoundError**
```bash
# Solución: Instalar dependencias
pip install -r requirements.txt
```

#### **Error: Puerto 8501 ocupado**
```bash
# Solución: Usar puerto diferente
streamlit run main_app.py --server.port 8502
```

#### **Error: Archivo de datos no encontrado**
- Los archivos JSON se crean automáticamente la primera vez
- Verificar permisos de escritura en la carpeta

#### **Logo no aparece**
1. Verificar que el archivo se llama `car.jpg`
2. Confirmar ubicación en la carpeta principal
3. Revisar formato de imagen (JPG/PNG)

### **Logs y Debugging**
- Revisar consola de Streamlit para errores
- Verificar archivos JSON para formato correcto
- Usar modo debug de Python si es necesario

## 📞 Soporte y Contacto

### **Contacto del Club**
- **📧 Email:** info@car.com.ar
- **📱 Teléfono:** (011) 4XXX-XXXX
- **🌐 Web:** www.clubargentinorugby.com.ar
- **📍 Dirección:** Av. del Libertador 1234, Buenos Aires

### **Soporte Técnico**
- **📧 Email:** desarrollo@car.com.ar
- **📋 Issues:** Reportar problemas y sugerencias
- **💬 Consultas:** Sobre funcionalidades y mejoras

## 📄 Licencia y Créditos

**© 2025 Club Argentino de Rugby**
Sistema de Digitalización Deportiva

**Desarrollado con:**
- 🐍 Python 3.11+
- ⚡ Streamlit 1.28+
- 📊 Plotly & Pandas
- 🎨 CSS3 & HTML5

**Versión:** 1.0.0
**Fecha:** Octubre 2025
**Desarrollador:** Sistema de Digitalización CAR

---

## 🏉 **"Digitalización de los Clubes - CAR 2025"**

*Sistema profesional para la gestión integral de la salud deportiva en el Club Argentino de Rugby*
# Reemplazar esta sección:
logo_label = tk.Label(logo_frame, text="🏉 LOGO", font=("Arial", 16, "bold"), 
                     bg='#2E4057', fg='white', relief='solid', bd=2, padx=10, pady=5)
logo_label.pack()

# Por esta nueva sección:
try:
    # Cargar y redimensionar el logo
    logo_image = Image.open("logo.png")
    logo_image = logo_image.resize((80, 80), Image.Resampling.LANCZOS)
    self.logo_photo = ImageTk.PhotoImage(logo_image)
    
    logo_label = tk.Label(logo_frame, image=self.logo_photo, bg='#2E4057')
    logo_label.pack()
except FileNotFoundError:
    # Si no se encuentra el logo, mostrar texto
    logo_label = tk.Label(logo_frame, text="🏉 CAR", font=("Arial", 16, "bold"), 
                         bg='#2E4057', fg='white', relief='solid', bd=2, padx=10, pady=5)
    logo_label.pack()
```

## Características de la página de login:

✅ **Diseño corporativo**: Colores azul oscuro y blanco
✅ **Logo**: Posicionado en la esquina superior derecha
✅ **Título**: "CLUB ARGENTINO DE RUGBY" prominente
✅ **Subtítulo**: "Digitalización de los Clubes" 
✅ **Formulario centrado**: Campos de usuario y contraseña
✅ **Botones**: Ingresar y Limpiar con colores distintivos
✅ **Funcionalidad**: Validación de campos y mensaje de error/éxito
✅ **Enlaces**: Recuperación de contraseña
✅ **Footer**: Información de copyright
✅ **Responsive**: Se adapta al tamaño de la ventana

## Para probar la aplicación:

1. Instala las dependencias: `pip install -r requirements.txt`
2. Ejecuta: `python Login.py`
3. Credenciales de prueba: usuario "admin", contraseña "admin"

## Personalización adicional:

- Cambiar colores en las variables de color (#2E4057, #28A745, etc.)
- Modificar fuentes y tamaños en los parámetros font
- Agregar más campos si es necesario
- Conectar con base de datos real para autenticación
- Agregar funcionalidad de "Recordar usuario"