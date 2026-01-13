# Guía de Solución de Problemas OCR

## Problema: El OCR no extrae datos correctamente

Si el sistema devuelve `None` para todos los campos, sigue estos pasos:

### 1. Verificar la Instalación de Tesseract

```bash
# Verificar que Tesseract está instalado
tesseract --version

# Verificar que el idioma español está disponible
tesseract --list-langs | grep spa
```

Si no está instalado:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang
```

### 2. Probar el Script de Diagnóstico

Usa el script de prueba para ver qué está extrayendo el OCR:

```bash
python test_ocr.py screenshots/tu-imagen.png
```

Esto mostrará:
- El texto RAW que extrae Tesseract
- Los datos estructurados que se extraen

### 3. Visualizar el Preprocesamiento

Ejecuta el script de debug para ver cómo se procesan las imágenes:

```bash
python debug_preprocessing.py screenshots/tu-imagen.png
```

Esto creará una carpeta `debug_images/` con diferentes versiones preprocesadas de tu imagen. Revisa cuál produce texto más legible.

### 4. Mejorar la Calidad de las Capturas

**Recomendaciones:**

- Usa capturas en formato PNG (mejor que JPG)
- Asegúrate de que la resolución sea alta (mínimo 1024x768)
- Captura con el zoom al 100% (no reducido)
- Verifica que el texto sea legible en la captura
- Evita capturas con demasiada compresión

### 5. Ajustar el Procesador OCR

Si las capturas tienen buena calidad pero aún no funciona, puedes:

#### Opción A: Usar el Procesador Mejorado

El sistema incluye un procesador mejorado. Para usarlo:

```python
from src.ocr_processor_enhanced import SicalOCRProcessorEnhanced

processor = SicalOCRProcessorEnhanced()
data = processor.extract_data('ruta/imagen.png')
```

#### Opción B: Ajustar Manualmente las Regiones

Si tu versión de SICAL II tiene un diseño diferente, puedes ajustar las regiones de extracción en `ocr_processor.py`:

```python
# En el método extract_with_regions, ajusta estas coordenadas:
regions = {
    'header': (y_inicio, y_fin, x_inicio, x_fin),
    # ... etc
}
```

### 6. Verificar el Formato de Números

El sistema espera números en formato español:
- Miles: punto (.) → `2.131.793`
- Decimales: coma (,) → `2.131.793,20`

Si tu sistema usa otro formato, ajusta el método `clean_number` en `ocr_processor.py`.

### 7. Logs Detallados

Para ver más detalles sobre qué está pasando, modifica el nivel de logging:

```python
# En src/ocr_processor.py, cambia:
logging.basicConfig(level=logging.DEBUG)  # En lugar de INFO
```

Luego ejecuta de nuevo y revisa los logs.

### 8. Patrones de Búsqueda

Si algunos campos se extraen pero otros no, es posible que el OCR esté leyendo mal los nombres de los campos. Puedes añadir variantes en `extract_data`:

```python
# Ejemplo: Si "Año" se lee como "Afio"
year_patterns = [
    r'A[ñn]o[:\s]+(\d{4})',
    r'Afio[:\s]+(\d{4})',
    r'Ano[:\s]+(\d{4})',  # Sin tilde
]
```

## Casos Específicos

### Caso 1: Solo Year y Concept se extraen

Esto indica que el OCR está leyendo la cabecera pero no el cuerpo. Posibles soluciones:

1. Aumentar el contraste en el preprocesamiento
2. Verificar que los campos no estén ocultos por elementos de UI
3. Usar el preprocesamiento "contrast" en lugar de "advanced"

### Caso 2: Los números se leen mal

Si los números se extraen pero con valores incorrectos:

1. Verifica el formato de números (punto/coma)
2. Revisa si hay espacios en los números
3. Ajusta el método `clean_number` para tu caso específico

### Caso 3: El texto se extrae pero los campos son None

Esto indica que los patrones de búsqueda no coinciden. Soluciones:

1. Ejecuta `test_ocr.py` y revisa el "RAW OCR OUTPUT"
2. Compara los nombres de campos en el OCR vs los patrones esperados
3. Añade variantes de los patrones en `extract_data`

## Contacto y Soporte

Si después de seguir estos pasos sigues teniendo problemas:

1. Ejecuta `python test_ocr.py` y guarda la salida
2. Ejecuta `python debug_preprocessing.py` y revisa las imágenes generadas
3. Abre un issue con:
   - La salida de `test_ocr.py`
   - Una captura de ejemplo (si no contiene datos sensibles)
   - Tu versión de Tesseract (`tesseract --version`)
   - Las imágenes generadas por `debug_preprocessing.py`
