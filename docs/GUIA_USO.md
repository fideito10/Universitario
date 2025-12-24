# 📋 Guía de Uso - Sistema CAR

## 🚀 Inicio Rápido

### 1. **Acceso al Sistema**
1. Abrir navegador y ir a: **http://localhost:8501**
2. **Credenciales de acceso:**
   - Usuario: `admin`
   - Contraseña: `admin123`
3. Hacer clic en **"🚀 Ingresar"**

### 2. **Navegación Principal**
Una vez dentro del sistema, verás el **sidebar izquierdo** con las siguientes opciones:
- 🏠 **Dashboard Principal** - Vista general del sistema
- 🏥 **Área Médica** - Gestión de lesiones y salud
- 🥗 **Área Nutrición** - Planes nutricionales y suplementos
- 🏋️ **Área Física** - Tests de fuerza y campo
- 🔗 **Google Sheets** - Sincronización con hojas de cálculo
- ⚙️ **Configuración** - Ajustes del usuario y sistema

---

## 🏥 Guía del Área Médica

### **Paso 1: Acceder al Área Médica**
1. En el sidebar, hacer clic en **"🏥 Área Médica"**
2. Se cargará el dashboard médico con las métricas actuales

### **Paso 2: Interpretar el Dashboard**
**📊 Métricas Principales (arriba de la pantalla):**
- **Total Lesiones:** Cantidad total registrada
- **En Recuperación:** Lesiones activas que requieren seguimiento
- **Recuperados:** Jugadores que ya fueron dados de alta
- **Casos Graves:** Lesiones que necesitan atención especial

### **Paso 3: Usar los Filtros**
**🔍 Filtros Disponibles:**
- **División:** Seleccionar "Primera", "Reserva", "Juveniles", etc.
- **Estado:** Filtrar por "En recuperación", "Recuperado" o "Todos"

### **Paso 4: Analizar los Gráficos**
**📈 Gráfico de Barras (izquierda):**
- Muestra cuántas lesiones hay por cada división
- Ayuda a identificar qué equipos necesitan más atención

**🥧 Gráfico Circular (derecha):**
- Distribución por severidad: Leve, Moderada, Grave
- Permite evaluar la gravedad general de las lesiones

### **Paso 5: Registrar Nueva Lesión**
1. **Bajar hasta la sección "➕ Registrar Nueva Lesión"**
2. **Completar los datos requeridos:**
   - 👤 **Nombre del Jugador:** Escribir nombre completo
   - 🏉 **División:** Seleccionar de la lista desplegable
   - 🩹 **Tipo de Lesión:** Ej: "Esguince de tobillo", "Distensión muscular"
   - ⚠️ **Severidad:** Elegir Leve, Moderada o Grave

3. **Completar información adicional:**
   - 📅 **Fecha de Ocurrencia:** Cuándo pasó la lesión
   - 🔮 **Recuperación Estimada:** Fecha aproximada de alta
   - 👨‍⚕️ **Médico Tratante:** Seleccionar del personal disponible
   - 📝 **Observaciones:** Detalles del tratamiento

4. **Hacer clic en "💾 Registrar Lesión"**
5. **Confirmación:** Aparecerá mensaje "✅ Lesión registrada exitosamente"

### **Datos de Ejemplo - Área Médica**
```
Jugador: Franco Silva
División: Juveniles
Tipo: Esguince de tobillo
Severidad: Leve
Fecha: Hoy
Recuperación: En 2 semanas
Doctor: Dr. García
Notas: Reposo y fisioterapia
```

---

## 🥗 Guía del Área Nutrición

### **Paso 1: Acceder al Área Nutrición**
1. En el sidebar, hacer clic en **"🥗 Área Nutrición"**
2. Se cargará el dashboard nutricional

### **Paso 2: Interpretar las Métricas**
**📊 Métricas Principales:**
- **Planes Activos:** Cantidad de planes nutricionales vigentes
- **Calorías Promedio:** Promedio calórico por división
- **Suplementos:** Cantidad de suplementos en uso
- **Divisiones:** Equipos con seguimiento nutricional

### **Paso 3: Usar la Calculadora Nutricional**
**🧮 Sección "Calculadora Nutricional":**

1. **Ingresar parámetros del jugador:**
   - ⚖️ **Peso:** En kilogramos (ej: 80)
   - 📏 **Altura:** En centímetros (ej: 180)
   - 🎂 **Edad:** En años (ej: 25)
   - 🏃‍♂️ **Nivel de Actividad:** Seleccionar intensidad
   - 🎯 **Objetivo:** Mantenimiento, Ganancia de masa, etc.

2. **Ver resultados automáticos:**
   - 🔥 **Calorías Diarias:** Requerimiento total
   - 🥩 **Proteínas:** Gramos necesarios
   - 🍞 **Carbohidratos:** Gramos recomendados
   - 🥑 **Grasas:** Gramos calculados

### **Paso 4: Crear Plan Nutricional**
1. **Ir a "➕ Crear Nuevo Plan Nutricional"**
2. **Completar datos básicos:**
   - 👤 **Nombre del Jugador:** Escribir nombre completo
   - 🏉 **División:** Seleccionar equipo
   - 🎯 **Tipo de Plan:** Elegir objetivo
   - 👩‍⚕️ **Nutricionista:** Asignar profesional

3. **Configurar objetivos nutricionales:**
   - 🔥 **Calorías objetivo:** Usar calculadora como referencia
   - 🥩 **Proteínas (g):** Según objetivo deportivo
   - 🍞 **Carbohidratos (g):** Para energía
   - 🥑 **Grasas (g):** Para balance hormonal

4. **Agregar observaciones y hacer clic en "💾 Crear Plan"**

### **Ejemplo de Plan Nutricional**
```
Jugador: Juan Pérez
División: Primera
Tipo: Ganancia de masa muscular
Calorías: 3500 kcal
Proteínas: 150g
Carbohidratos: 400g
Grasas: 120g
Nutricionista: Lic. María López
Notas: Plan para aumento de peso controlado
```

---

## 📊 Interpretación de Gráficos

### **📈 Gráfico de Barras - Lesiones por División**
- **Eje X:** Divisiones del club (Primera, Reserva, etc.)
- **Eje Y:** Cantidad de lesiones
- **Interpretación:** 
  - Barras altas = Más lesiones en esa división
  - Útil para identificar equipos que necesitan más atención médica

### **🥧 Gráfico Circular - Severidad**
- **Verde:** Lesiones leves (menor preocupación)
- **Amarillo:** Lesiones moderadas (seguimiento normal)
- **Rojo:** Lesiones graves (atención prioritaria)

### **📊 Gráfico de Calorías por División**
- Muestra el promedio calórico que consume cada división
- Útil para comparar necesidades nutricionales entre equipos
- Las divisiones superiores generalmente requieren más calorías

---

## 🔧 Funciones Avanzadas

### **📤 Exportar Datos**
*Funcionalidad en desarrollo - próximamente disponible*

### **🔄 Actualizar Información**
- Los datos se guardan automáticamente al registrar
- Para ver cambios, refrescar la página (F5)
- Los gráficos se actualizan automáticamente

### **🔍 Búsqueda y Filtros**
- Usar los filtros en cada área para encontrar información específica
- Los filtros se aplican a tablas y gráficos simultáneamente

---

## ❓ Preguntas Frecuentes

### **🏥 Área Médica**

**Q: ¿Puedo modificar una lesión ya registrada?**
A: Actualmente no desde la interfaz. Se puede editar manualmente el archivo `medical_records.json`

**Q: ¿Qué pasa si no sé la fecha exacta de recuperación?**
A: Puedes poner una estimación aproximada. Se puede actualizar después.

**Q: ¿Cómo elimino una lesión registrada por error?**
A: Por ahora se debe editar manualmente el archivo de datos o contactar al administrador.

### **🥗 Área Nutrición**

**Q: ¿Los cálculos nutricionales son precisos?**
A: Son estimaciones basadas en fórmulas estándar. Siempre consultar con nutricionista profesional.

**Q: ¿Puedo crear planes para jugadores de otras divisiones?**
A: Sí, todas las divisiones están disponibles en el selector.

**Q: ¿Se pueden registrar suplementos individualmente?**
A: Actualmente se registran junto con los planes. Funcionalidad individual en desarrollo.

### **⚙️ Sistema General**

**Q: ¿Se guarda mi sesión si cierro el navegador?**
A: Dependiendo de la configuración del checkbox "Recordarme" al hacer login.

**Q: ¿Puedo usar el sistema desde mi celular?**
A: Sí, el diseño es responsive y funciona en dispositivos móviles.

**Q: ¿Los datos están seguros?**
A: Se almacenan localmente en archivos JSON con contraseñas encriptadas.

---

## 🚨 Solución de Problemas Comunes

### **Problema: No puedo ingresar al sistema**
**Solución:**
1. Verificar credenciales: `admin` / `admin123`
2. Asegurar que no hay espacios extra
3. Probar refrescar la página

### **Problema: Los gráficos no cargan**
**Solución:**
1. Verificar conexión a internet
2. Refrescar página (F5)
3. Verificar que hay datos registrados

### **Problema: Error al registrar datos**
**Solución:**
1. Completar todos los campos obligatorios
2. Verificar formato de fechas
3. Probar con datos más simples primero

### **Problema: El sistema va lento**
**Solución:**
1. Cerrar pestañas innecesarias del navegador
2. Refrescar la página
3. Verificar que no hay otros programas pesados corriendo

---

## 📞 Contacto y Soporte

### **🆘 Si necesitas ayuda:**
1. **📧 Email:** desarrollo@car.com.ar
2. **📱 Teléfono:** (011) 4XXX-XXXX
3. **💬 Consultas:** Reportar problemas o sugerencias

### **📋 Para reportar errores:**
1. Describir qué estabas haciendo
2. Incluir mensaje de error (si aparece)
3. Mencionar navegador y dispositivo usado

---

## 🎯 Consejos de Uso Eficiente

### **🏥 Para el Área Médica:**
- ✅ Registrar lesiones inmediatamente después de que ocurran
- ✅ Usar descripciones claras y específicas
- ✅ Actualizar el estado cuando los jugadores se recuperen
- ✅ Revisar regularmente las métricas para identificar patrones

### **🥗 Para el Área Nutrición:**
- ✅ Usar la calculadora antes de crear planes manuales
- ✅ Ajustar objetivos según la temporada deportiva
- ✅ Revisar y actualizar planes regularmente
- ✅ Coordinar con el personal médico para jugadores lesionados

### **📊 Para el Dashboard:**
- ✅ Revisar métricas semanalmente
- ✅ Usar filtros para análisis específicos
- ✅ Comparar datos entre divisiones
- ✅ Tomar decisiones basadas en datos visuales

---

## 🏋️ Guía del Área Física

### **Paso 1: Acceder al Área Física**
1. En el sidebar, hacer clic en **"🏋️ Área Física"**
2. Se cargará el dashboard físico con 5 pestañas principales

### **Paso 2: Interpretar el Dashboard Físico**
**📊 Métricas Principales:**
- **💪 Tests de Fuerza:** Total de evaluaciones de fuerza registradas
- **🏃 Tests de Campo:** Total de evaluaciones de campo registradas
- **👥 Jugadores Evaluados:** Cantidad de jugadores únicos evaluados
- **📅 Tests Este Mes:** Evaluaciones realizadas en el mes actual

### **Paso 3: Registrar Tests de Fuerza**

#### **💪 Pestaña "Tests de Fuerza":**
1. **Ir a la sub-pestaña "➕ Nuevo Test"**
2. **Completar información del jugador:**
   - 👤 **Nombre del Jugador**
   - 🏉 **División**
   - 📅 **Fecha del Test**
   - 👨‍⚕️ **Preparador Físico**

3. **Datos del test:**
   - 💪 **Tipo de Test:** (Bench Press, Squat, Deadlift, etc.)
   - ⚖️ **Peso (kg):** Peso levantado
   - 🔢 **Repeticiones:** Cantidad realizada
   - 📊 **Series:** Número de series

4. **Mediciones adicionales (opcionales):**
   - ⚖️ **Peso Corporal:** Peso del jugador
   - 📏 **Altura:** Altura en cm
   - 🧮 **% Grasa Corporal**
   - 💪 **% Masa Muscular**

5. **Hacer clic en "💾 Guardar Test de Fuerza"**

**✨ El sistema calcula automáticamente el 1RM estimado usando la fórmula de Brzycki**

### **Paso 4: Registrar Tests de Campo**

#### **🏃 Pestaña "Tests de Campo":**
1. **Ir a la sub-pestaña "➕ Nuevo Test"**
2. **Completar información básica igual que en tests de fuerza**
3. **Seleccionar tipo de test:**
   - **Sprint:** 10m, 20m, 40m, 100m
   - **Resistencia:** Yo-Yo Test, Test de Cooper
   - **Agilidad:** T-Test
   - **Saltos:** Vertical, Horizontal
   - **Velocidad:** Tests específicos

4. **Resultado según tipo:**
   - ⏱️ **Sprints:** Tiempo en segundos
   - 📏 **Resistencia:** Distancia en metros
   - 📏 **Saltos:** Altura/distancia en cm

5. **Condiciones del test:**
   - ☀️ **Clima:** Soleado, Nublado, Lluvia, Viento
   - 🌡️ **Temperatura:** En grados Celsius
   - 🏟️ **Superficie:** Césped Natural/Sintético, Pista, Gimnasio
   - 💧 **Humedad:** Porcentaje

### **Paso 5: Análisis por Jugador**

#### **👥 Pestaña "Por Jugador":**
1. **Seleccionar jugador** del dropdown
2. **Ver métricas resumidas:**
   - Cantidad de tests de fuerza
   - Cantidad de tests de campo
   - División actual

3. **Analizar evolución:**
   - Gráficos de progreso por tipo de test
   - Comparación de resultados en el tiempo
   - Identificar mejoras o retrocesos

### **Paso 6: Revisar Tests Registrados**

#### **📋 Sub-pestaña "Lista de Tests":**
1. **Usar filtros para buscar:**
   - **🏉 Por División:** Filtrar por categoría
   - **💪/🏃 Por Tipo:** Filtrar por tipo de test específico
   - **👤 Por Jugador:** Ver tests de un jugador específico

2. **Analizar datos:** Ver tabla completa con todos los resultados

### **Ejemplo de Test de Fuerza**
```
Jugador: Juan Pérez
División: Primera
Fecha: 2025-10-08
Tipo: Bench Press
Peso: 80kg
Repeticiones: 8
Series: 3
1RM Estimado: 100kg (calculado automáticamente)
Preparador: Prof. García
Observaciones: Excelente técnica, progreso notable
```

### **Ejemplo de Test de Campo**
```
Jugador: Carlos López
División: Reserva
Fecha: 2025-10-08
Tipo: Sprint 40m
Resultado: 5.85 segundos
Clima: Soleado
Temperatura: 22°C
Superficie: Césped Natural
Preparador: Prof. Martínez
Observaciones: Tiempo excelente para su categoría
```

---

## 🔗 Guía de Google Sheets

### **Paso 1: Configuración Inicial**
1. **Acceder a Google Sheets:**
   - En el sidebar, hacer clic en **"🔗 Google Sheets"**
   - Primera vez verás instrucciones de configuración

2. **Configurar Credenciales (Solo una vez):**
   - Ir a: https://console.cloud.google.com/
   - Crear proyecto: "CAR Rugby Club"
   - Habilitar APIs: Google Sheets API y Google Drive API
   - Crear Service Account y descargar JSON
   - Subir archivo en la aplicación

### **Paso 2: Crear y Preparar Google Sheets**
1. **Crear nueva hoja en Google Sheets**
2. **Usar estructura recomendada:**

**Para Datos Médicos:**
```
jugador | division | lesion | severidad | fecha | estado | observaciones
```

**Para Datos Nutricionales:**
```
jugador | division | plan | calorias | proteinas | carbohidratos | grasas | observaciones
```

3. **Compartir la hoja:**
   - Clic en "Compartir"
   - Agregar email del service account
   - Dar permisos de "Editor"

### **Paso 3: Sincronizar Datos**

#### **🏥 Sincronización Médica:**
1. **Ir a la tab "� Sincronizar Médico"**
2. **Pegar URL** de tu Google Sheet
3. **Seleccionar Doctor** responsable
4. **Probar conexión** con el botón "🔍 Probar Conexión"
5. **Elegir hoja de trabajo** si tienes múltiples tabs
6. **Ver vista previa** de los datos
7. **Hacer clic en "🔄 Sincronizar Datos Médicos"**

#### **🥗 Sincronización Nutricional:**
1. **Ir a la tab "🥗 Sincronizar Nutrición"**
2. **Pegar URL** de tu Google Sheet nutricional
3. **Seleccionar Nutricionista** responsable
4. **Probar conexión** y seleccionar hoja
5. **Sincronizar** con el botón correspondiente

### **Paso 4: Monitorear Conexiones**
1. **Ir a la tab "📊 Estado de Conexiones"**
2. **Ver todas las hojas conectadas:**
   - Conexiones médicas activas
   - Conexiones nutricionales activas
   - Fecha de última sincronización
3. **Opciones disponibles:**
   - **🔍 Probar:** Verificar si la conexión sigue activa
   - **🔄 Sync:** Re-sincronizar datos manualmente

### **Paso 5: Configuración Avanzada**
**En la tab "⚙️ Configuración":**
- **Sincronización automática** (opcional)
- **Mapeo de columnas personalizado**
- **Ver plantillas de ejemplo**
- **Limpiar conexiones** si es necesario

### **📋 Plantillas y Estructura**

#### **Estructura Médica Recomendada:**
```
| jugador         | division | lesion            | severidad | fecha      | estado        | observaciones      |
|-----------------|----------|-------------------|-----------|------------|---------------|--------------------|
| Juan Pérez      | Primera  | Esguince tobillo  | Moderada  | 2025-10-01 | En tratamiento| Evolución favorable|
| Carlos González | Reserva  | Contusión muscular| Leve      | 2025-10-05 | Recuperado    | Alta médica dada   |
```

#### **Estructura Nutricional Recomendada:**
```
| jugador    | division | plan                    | calorias | proteinas | carbohidratos | grasas | observaciones        |
|------------|----------|-------------------------|----------|-----------|---------------|--------|----------------------|
| Juan Pérez | Primera  | Aumento masa muscular   | 3200     | 180       | 400           | 100    | Buena adherencia     |
| Luis López | M19      | Reducción grasa         | 2400     | 130       | 280           | 70     | Requiere seguimiento |
```

### **🔧 Solución de Problemas**

#### **❌ Error de Conexión:**
- ✅ Verificar que la URL sea correcta
- ✅ Comprobar que la hoja esté compartida
- ✅ Confirmar permisos de "Editor"
- ✅ Validar que el service account tenga acceso

#### **❌ Datos No Aparecen:**
- ✅ Revisar nombres de columnas (deben coincidir)
- ✅ Verificar que no hay filas vacías entre datos
- ✅ Comprobar formato de fechas (YYYY-MM-DD)
- ✅ Validar que los datos no estén en otra hoja

#### **❌ Error de Formato:**
- ✅ Fechas: usar formato YYYY-MM-DD
- ✅ Números: sin puntos de miles, usar punto decimal
- ✅ Texto: evitar caracteres especiales
- ✅ Divisiones: usar nombres estándar

### **💡 Consejos y Mejores Prácticas**

#### **🏥 Para Médicos:**
- ✅ Actualizar la hoja diariamente
- ✅ Usar terminología médica estándar
- ✅ Incluir fechas de seguimiento
- ✅ Mantener observaciones detalladas

#### **🥗 Para Nutricionistas:**
- ✅ Revisar planes semanalmente
- ✅ Ajustar según progreso del atleta
- ✅ Coordinar con el área médica
- ✅ Documentar cambios importantes

#### **⚡ Para Administradores:**
- ✅ Sincronizar datos regularmente
- ✅ Monitorear estado de conexiones
- ✅ Hacer backup de configuraciones
- ✅ Capacitar a profesionales en el uso

### **🔒 Seguridad y Privacidad**
- 🔐 Solo personal autorizado accede a las hojas
- 🔐 Datos médicos protegidos según normativas
- 🔐 Credenciales de Google Cloud seguras
- 🔐 Acceso controlado por roles de usuario

---

**🏉 ¡Sistema CAR totalmente integrado con Google Sheets!**

*Esta guía te ayudará a aprovechar al máximo el sistema CAR. Para dudas adicionales, no dudes en contactar al equipo de soporte.*