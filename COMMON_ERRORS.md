# Errores Comunes y Soluciones

## Error: "numpy.dtype size changed"

### Síntoma
```
ValueError: numpy.dtype size changed, may indicate binary incompatibility.
Expected 96 from C header, got 88 from PyObject
```

### Causa
Incompatibilidad entre las versiones de numpy y pandas. Pandas fue compilado con una versión diferente de numpy.

### Solución Rápida

**Opción 1: Usar el script de fix (Recomendado)**

Windows:
```cmd
fix_dependencies.bat
```

Linux/Mac:
```bash
chmod +x fix_dependencies.sh
./fix_dependencies.sh
```

Multiplataforma (Python):
```bash
python fix_dependencies.py
```

**Opción 2: Manual**

```bash
# 1. Desinstalar numpy y pandas
pip uninstall -y numpy pandas

# 2. Reinstalar en orden (numpy primero)
pip install numpy==1.26.4
pip install pandas==2.2.1

# 3. Verificar
python -c "import numpy, pandas; print('OK')"
```

**Opción 3: Reinstalar todo el entorno**

Windows:
```cmd
# Eliminar entorno virtual
rmdir /s /q venv

# Crear nuevo entorno
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Linux/Mac:
```bash
# Eliminar entorno virtual
rm -rf venv

# Crear nuevo entorno
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Error: "TesseractNotFoundError"

### Síntoma
```
pytesseract.pytesseract.TesseractNotFoundError: tesseract is not installed
```

### Causa
Tesseract OCR no está instalado en el sistema o no está en el PATH.

### Solución

**Windows:**
1. Descargar instalador de: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar (anotar la ruta de instalación)
3. Añadir al PATH o configurar en el código:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

**Mac:**
```bash
brew install tesseract tesseract-lang
```

**Verificar instalación:**
```bash
tesseract --version
tesseract --list-langs | grep spa
```

---

## Error: "EasyOCR models not found"

### Síntoma
EasyOCR se queda descargando modelos o falla al inicializar.

### Causa
Primera ejecución de EasyOCR - necesita descargar modelos (~80MB).

### Solución
1. Asegurar conexión a Internet estable
2. Esperar a que termine la descarga (puede tardar varios minutos)
3. Los modelos se guardan en `~/.EasyOCR/` y solo se descargan una vez

Si la descarga falla:
```bash
# Eliminar modelos parcialmente descargados
rm -rf ~/.EasyOCR/model/

# O en Windows
rmdir /s /q %USERPROFILE%\.EasyOCR\model\

# Reintentar
python test_easyocr.py
```

---

## Error: "Module not found"

### Síntoma
```
ModuleNotFoundError: No module named 'xxx'
```

### Causa
Dependencias no instaladas o entorno virtual no activado.

### Solución

**1. Verificar que el entorno virtual está activado**

Windows:
```cmd
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

Deberías ver `(venv)` al inicio del prompt.

**2. Instalar/reinstalar dependencias**
```bash
pip install -r requirements.txt
```

**3. Si persiste, reinstalar el módulo específico**
```bash
pip install --force-reinstall nombre-del-modulo
```

---

## Error: "Permission denied" al ejecutar scripts

### Síntoma (Linux/Mac)
```
bash: ./script.sh: Permission denied
```

### Solución
```bash
chmod +x script.sh
./script.sh
```

O ejecutar con python:
```bash
python script.py
```

---

## Error: "Cannot create directory" en Windows

### Síntoma
```
PermissionError: [WinError 5] Access is denied
```

### Causa
El antivirus o permisos de Windows están bloqueando la creación de carpetas.

### Solución
1. Ejecutar como administrador
2. Añadir excepción en el antivirus
3. Verificar permisos de la carpeta del proyecto
4. Usar una ubicación diferente (ej: `C:\Users\tu-usuario\Documents\`)

---

## Error: OCR no extrae ningún dato (todos None)

### Síntoma
```
year                          : None
concept                       : None
...todos los campos en None...
```

### Causa
Puede ser calidad de imagen, OCR no funciona, o patrones no coinciden.

### Diagnóstico

**1. Verificar que OCR lee algo:**
```bash
python test_ocr.py screenshots/tu-imagen.png
```

Revisa la sección "RAW OCR OUTPUT". Si está vacío, el OCR no lee nada.

**2. Ver preprocesamiento:**
```bash
python debug_preprocessing.py screenshots/tu-imagen.png
```

Revisa las imágenes en `debug_images/` para ver cuál funciona mejor.

**3. Probar con EasyOCR:**
```bash
pip install easyocr
python test_easyocr.py
```

### Soluciones

1. **Mejorar calidad de captura:**
   - Usar formato PNG (no JPG)
   - Capturar a resolución nativa (100% zoom)
   - Asegurar que el texto es legible

2. **Usar EasyOCR:**
   ```bash
   pip install easyocr
   ```
   El sistema lo usará automáticamente.

3. **Ajustar patrones** (ver TROUBLESHOOTING.md)

---

## Error: "Address already in use" (Dashboard)

### Síntoma
```
OSError: [Errno 48] Address already in use
```

### Causa
El puerto 8501 (Streamlit) ya está en uso.

### Solución

**Opción 1: Cerrar la instancia existente**

Windows:
```cmd
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

Linux/Mac:
```bash
lsof -ti:8501 | xargs kill -9
```

**Opción 2: Usar otro puerto**
```bash
streamlit run src/dashboard.py --server.port 8502
```

---

## Error: Database locked

### Síntoma
```
sqlite3.OperationalError: database is locked
```

### Causa
Múltiples procesos intentan acceder a la base de datos simultáneamente.

### Solución
1. Cerrar todos los procesos (monitor, dashboard)
2. Esperar unos segundos
3. Reiniciar uno por uno

Si persiste:
```bash
# Backup de la base de datos
cp data/sical_tracking.db data/sical_tracking.db.backup

# Eliminar locks
rm -f data/sical_tracking.db-journal
```

---

## Necesitas más ayuda?

1. Ejecuta el diagnóstico apropiado:
   - `python test_ocr.py` para problemas de OCR
   - `python debug_preprocessing.py` para problemas de imagen
   - `python test_easyocr.py` para probar EasyOCR

2. Revisa los logs del monitor (ejecutar en modo verbose)

3. Consulta TROUBLESHOOTING.md para más detalles

4. Abre un issue en GitHub con:
   - El error completo
   - Tu sistema operativo
   - Versiones de Python y paquetes
   - Resultado de los scripts de diagnóstico
