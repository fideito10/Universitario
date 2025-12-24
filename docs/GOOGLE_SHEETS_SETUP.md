# 🔐 Configuración de Google Sheets para CAR

## 📋 Guía Paso a Paso para Configurar Google Cloud

### 🚀 Paso 1: Crear Proyecto en Google Cloud

1. **Ir a Google Cloud Console:**
   - Visita: https://console.cloud.google.com/
   - Inicia sesión con tu cuenta de Google

2. **Crear Nuevo Proyecto:**
   - Clic en el selector de proyectos (arriba izquierda)
   - Clic en "Nuevo Proyecto"
   - Nombre: `CAR Rugby Club`
   - Clic en "Crear"

### 🔧 Paso 2: Habilitar APIs Necesarias

1. **Ir a la Biblioteca de APIs:**
   - Menú hamburguesa → "APIs y servicios" → "Biblioteca"

2. **Habilitar Google Sheets API:**
   - Buscar "Google Sheets API"
   - Clic en "Google Sheets API"
   - Clic en "Habilitar"

3. **Habilitar Google Drive API:**
   - Buscar "Google Drive API"
   - Clic en "Google Drive API"
   - Clic en "Habilitar"

### 🔑 Paso 3: Crear Service Account

1. **Ir a Credenciales:**
   - Menú → "APIs y servicios" → "Credenciales"

2. **Crear Credenciales:**
   - Clic en "+ CREAR CREDENCIALES"
   - Seleccionar "Cuenta de servicio"

3. **Configurar Service Account:**
   - Nombre: `car-service-account`
   - ID: `car-service-account`
   - Descripción: `Service Account para CAR Rugby Club`
   - Clic en "Crear y continuar"

4. **Asignar Rol (Opcional):**
   - Puedes omitir este paso
   - Clic en "Continuar"

5. **Finalizar:**
   - Clic en "Listo"

### 📥 Paso 4: Descargar Archivo de Credenciales

1. **Buscar tu Service Account:**
   - En la lista de credenciales, encontrar `car-service-account`

2. **Generar Clave:**
   - Clic en el ícono de lápiz (editar)
   - Ir a la pestaña "Claves"
   - Clic en "Agregar clave" → "Crear clave nueva"
   - Seleccionar formato "JSON"
   - Clic en "Crear"

3. **Guardar Archivo:**
   - Se descargará automáticamente un archivo JSON
   - Renombrarlo a: `car_google_credentials.json`
   - Guardar en: `c:\Users\dell\Desktop\Car\`

### 🔗 Paso 5: Configurar Google Sheets

1. **Crear Nueva Hoja:**
   - Ir a: https://sheets.google.com/
   - Crear nueva hoja de cálculo

2. **Agregar Encabezados:**
   
   **Para Datos Médicos:**
   ```
   jugador | division | lesion | severidad | fecha | estado | observaciones
   ```
   
   **Para Datos Nutricionales:**
   ```
   jugador | division | plan | calorias | proteinas | carbohidratos | grasas | observaciones
   ```

3. **Compartir la Hoja:**
   - Clic en "Compartir" (botón azul arriba derecha)
   - En "Agregar personas y grupos":
     - Pegar el **client_email** del archivo JSON descargado
     - Ejemplo: `car-service-account@car-rugby-club-xxxxx.iam.gserviceaccount.com`
   - Seleccionar permisos: **Editor**
   - Desmarcar "Notificar a las personas"
   - Clic en "Enviar"

### ⚙️ Paso 6: Configurar en la Aplicación CAR

1. **Subir Credenciales:**
   - Abrir aplicación CAR: http://localhost:8501
   - Ir a "🔗 Google Sheets"
   - Subir el archivo `car_google_credentials.json`

2. **Conectar Hoja:**
   - Copiar URL de tu Google Sheet
   - Pegar en el campo correspondiente
   - Seleccionar profesional
   - Probar conexión
   - Sincronizar datos

## 🎯 Plantillas Recomendadas

### 📋 Plantilla Médica Completa

```
| jugador         | division | lesion              | severidad | fecha      | estado         | tratamiento           | observaciones           |
|-----------------|----------|---------------------|-----------|------------|----------------|-----------------------|------------------------|
| Juan Pérez      | Primera  | Esguince de tobillo | Moderada  | 2025-10-01 | En tratamiento | Fisioterapia diaria   | Evolución favorable    |
| Carlos González | Reserva  | Contusión muscular  | Leve      | 2025-10-05 | Recuperado     | Reposo 48hs          | Alta médica dada       |
| Luis Martínez   | M19      | Fractura de dedo    | Grave     | 2025-10-07 | En tratamiento | Cirugía + rehab      | Seguimiento semanal    |
```

### 🥗 Plantilla Nutricional Completa

```
| jugador      | division | plan                      | calorias | proteinas | carbohidratos | grasas | peso | altura | objetivo                | observaciones         |
|--------------|----------|---------------------------|----------|-----------|---------------|--------|------|--------|-------------------------|-----------------------|
| Juan Pérez   | Primera  | Aumento de masa muscular  | 3200     | 180       | 400           | 100    | 85   | 182    | Ganar 3kg masa muscular | Buena adherencia      |
| Carlos López | Reserva  | Mantenimiento             | 2800     | 150       | 350           | 85     | 78   | 175    | Mantener peso actual    | Atleta disciplinado   |
| Luis García  | M19      | Reducción de grasa        | 2400     | 130       | 280           | 70     | 72   | 170    | Perder 2kg de grasa     | Requiere seguimiento  |
```

## ⚠️ Errores Comunes y Soluciones

### ❌ Error: "403 Forbidden"
**Causa:** La hoja no está compartida correctamente
**Solución:**
- Verificar que el `client_email` esté agregado como editor
- Comprobar que los permisos sean "Editor", no "Visor"

### ❌ Error: "Spreadsheet not found"
**Causa:** URL incorrecta o hoja eliminada
**Solución:**
- Verificar que la URL sea correcta
- Comprobar que la hoja exista y sea accesible

### ❌ Error: "No data found"
**Causa:** Hoja vacía o nombres de columnas incorrectos
**Solución:**
- Verificar que hay datos en la hoja
- Comprobar que los nombres de columnas coincidan

### ❌ Error de conexión general
**Causa:** Credenciales incorrectas o APIs no habilitadas
**Solución:**
- Verificar que las APIs estén habilitadas
- Revisar que el archivo JSON sea correcto
- Comprobar conexión a internet

## 🔒 Seguridad y Mejores Prácticas

### ✅ Recomendaciones de Seguridad:
- **No compartir** el archivo de credenciales públicamente
- **Limitar acceso** solo al personal autorizado
- **Revisar permisos** regularmente
- **Usar nombres descriptivos** para hojas y proyectos

### ✅ Mejores Prácticas:
- **Backup regular** de las hojas importantes
- **Documentar cambios** en observaciones
- **Mantener formato consistente** en fechas y números
- **Sincronizar datos** al menos diariamente

## 📞 Soporte Técnico

Si necesitas ayuda con la configuración:

- 📧 **Email:** admin@car.com.ar
- 📱 **WhatsApp:** (011) 4XXX-XXXX
- 🕐 **Horario:** Lunes a Viernes 9:00-18:00
- 💬 **Discord:** CAR Rugby Club - Canal #soporte-tecnico

## 🎓 Recursos Adicionales

- [Documentación Google Sheets API](https://developers.google.com/sheets/api)
- [Guía Google Cloud Console](https://cloud.google.com/docs)
- [Video Tutorial CAR](https://youtube.com/car-rugby-tutorial) *(próximamente)*

---

**🏉 ¡Sistema CAR completamente configurado y listo para usar!**