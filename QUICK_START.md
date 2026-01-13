# Guía Rápida para Probar el OCR Mejorado

## Paso 1: Verificar Tesseract

```bash
# Verificar que Tesseract está instalado
tesseract --version

# Verificar idioma español
tesseract --list-langs | grep spa
```

Si no aparece `spa`, instálalo:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr-spa

# macOS
brew install tesseract-lang

# Windows: descargar paquete de idioma desde
# https://github.com/tesseract-ocr/tessdata
```

## Paso 2: Colocar tu Captura

```bash
# Coloca tu captura en la carpeta screenshots/
cp "Captura de pantalla 2026-01-13 113036.png" screenshots/
```

## Paso 3: Probar la Extracción

### Opción A: Probar con el procesador mejorado

```bash
python test_ocr.py screenshots/"Captura de pantalla 2026-01-13 113036.png"
```

Esto mostrará:
- El texto RAW que extrae el OCR
- Los datos estructurados extraídos

### Opción B: Ver el preprocesamiento

```bash
python debug_preprocessing.py screenshots/"Captura de pantalla 2026-01-13 113036.png"
```

Esto generará múltiples versiones preprocesadas en `debug_images/`. Revisa cuál tiene el texto más legible.

### Opción C: Probar con EasyOCR (Más Robusto)

```bash
# Instalar EasyOCR (primera vez solamente)
pip install easyocr

# Ejecutar
python src/ocr_easyocr.py
```

EasyOCR suele funcionar mejor con interfaces gráficas complejas.

## Paso 4: Interpretar Resultados

### Si el test_ocr.py muestra texto pero datos None:

Significa que el OCR está leyendo pero los patrones no coinciden. Posibles causas:
- Los nombres de campos están mal escritos en el OCR
- El layout es diferente al esperado
- Los números tienen un formato diferente

**Solución**: Revisa el "RAW OCR OUTPUT" y compara con lo que esperamos extraer.

### Si el test_ocr.py no muestra texto:

Significa que Tesseract no puede leer la imagen. Posibles causas:
- Tesseract no está instalado correctamente
- La imagen tiene muy bajo contraste
- El texto es muy pequeño

**Solución**:
1. Revisa las imágenes en `debug_images/` después de ejecutar `debug_preprocessing.py`
2. Prueba con EasyOCR

### Si algunos campos se extraen pero otros no:

El OCR está funcionando parcialmente.

**Solución**:
- Verifica que los nombres de campo en la captura coinciden con los esperados
- Revisa el TROUBLESHOOTING.md para ajustar patrones específicos

## Paso 5: Usar el Monitor con las Mejoras

Una vez que confirmes que la extracción funciona:

```bash
# Terminal 1: Iniciar monitor
python run_monitor.py

# Terminal 2: Iniciar dashboard
python run_dashboard.py
```

## Tips para Mejores Resultados

1. **Calidad de imagen**: PNG > JPG
2. **Resolución**: Mínimo 1024x768
3. **Zoom**: 100% (no reducido)
4. **Limpieza**: Sin elementos superpuestos
5. **Formato**: Asegúrate de capturar toda la ventana SICAL

## Si Nada Funciona

Consulta [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para:
- Diagnóstico avanzado
- Ajustar patrones de extracción
- Configurar regiones personalizadas
- Contactar soporte con logs
