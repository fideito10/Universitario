# 🏉 Guía de Implementación - Logo del CAR

## Instrucciones para el Logo

Para que el logo del Club Argentino de Rugby aparezca correctamente en la aplicación:

### 1. Preparar la Imagen del Logo
- **Formato:** JPG, PNG, o SVG
- **Tamaño recomendado:** 300x300 píxeles
- **Nombre del archivo:** `car.jpg` (o `car.png`)
- **Ubicación:** Carpeta principal del proyecto

### 2. Optimización de la Imagen
```python
# Script para redimensionar automáticamente el logo
from PIL import Image
import os

def optimize_logo(input_path, output_path="car.jpg", size=(300, 300)):
    """Optimizar logo para la aplicación"""
    try:
        with Image.open(input_path) as img:
            # Convertir a RGB si es necesario
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionar manteniendo proporción
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Crear imagen cuadrada con fondo blanco
            new_img = Image.new('RGB', size, (255, 255, 255))
            
            # Centrar el logo
            x = (size[0] - img.width) // 2
            y = (size[1] - img.height) // 2
            new_img.paste(img, (x, y))
            
            # Guardar optimizado
            new_img.save(output_path, 'JPEG', quality=90)
            print(f"✅ Logo optimizado y guardado como {output_path}")
            
    except Exception as e:
        print(f"❌ Error al procesar la imagen: {e}")

# Uso del script
# optimize_logo("logo_original.png", "car.jpg")
```

### 3. Verificar la Implementación
Una vez que agregues la imagen `car.jpg` a la carpeta del proyecto, el sistema:

1. **Detectará automáticamente** el archivo de logo
2. **Redimensionará** la imagen para el display
3. **Posicionará** el logo en la esquina superior derecha
4. **Mantendrá** un placeholder si no encuentra la imagen

### 4. Formatos de Logo Soportados

#### Formato Principal
```
car.jpg         # Formato principal (recomendado)
```

#### Formatos Alternativos
```python
# El sistema busca en este orden:
logo_files = [
    "car.jpg",
    "car.png", 
    "car.jpeg",
    "logo.jpg",
    "logo.png"
]
```

### 5. Ejemplo de Código para Cargar Múltiples Formatos

```python
def find_logo():
    """Buscar archivo de logo en múltiples formatos"""
    logo_files = ["car.jpg", "car.png", "car.jpeg", "logo.jpg", "logo.png"]
    
    for logo_file in logo_files:
        if os.path.exists(logo_file):
            return logo_file
    
    return None

# Usar en la aplicación
logo_path = find_logo()
if logo_path:
    image = Image.open(logo_path)
    st.image(image, width=100)
```

### 6. Troubleshooting

#### Problema: Logo no aparece
**Solución:**
1. Verificar que el archivo se llama exactamente `car.jpg`
2. Confirmar que está en la carpeta principal del proyecto
3. Revisar permisos de lectura del archivo

#### Problema: Logo se ve distorsionado
**Solución:**
1. Usar el script de optimización proporcionado
2. Asegurar que la imagen original tenga buena resolución
3. Convertir a formato JPG si es PNG con transparencia

#### Problema: Logo muy grande o pequeño
**Solución:**
1. Ajustar el parámetro `width` en `st.image()`
2. Modificar el tamaño en el CSS personalizado
3. Usar el script de redimensionamiento

### 7. Personalización Avanzada

#### Cambiar Posición del Logo
```python
# En lugar de columnas, usar CSS
st.markdown("""
<div style="position: absolute; top: 20px; right: 20px; z-index: 999;">
    <img src="data:image/jpeg;base64,{}" width="80">
</div>
""".format(base64_image), unsafe_allow_html=True)
```

#### Logo Responsivo
```css
/* Agregar al CSS personalizado */
.logo-responsive {
    max-width: 100px;
    width: 100%;
    height: auto;
}

@media (max-width: 768px) {
    .logo-responsive {
        max-width: 60px;
    }
}
```

### 8. Logo con Animación
```python
# Logo con efecto hover
st.markdown("""
<style>
.logo-animation {
    transition: transform 0.3s ease;
}

.logo-animation:hover {
    transform: scale(1.1);
}
</style>
""", unsafe_allow_html=True)
```

---

## 📝 Nota Importante

Una vez que agregues el archivo `car.jpg` con el logo oficial del Club Argentino de Rugby, la aplicación automáticamente lo detectará y lo mostrará en la esquina superior derecha de la pantalla de login.

El sistema está diseñado para funcionar tanto con como sin el logo, manteniendo un placeholder profesional cuando la imagen no está disponible.