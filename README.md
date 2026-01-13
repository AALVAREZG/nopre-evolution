# SICAL II - Sistema de Seguimiento Automático

Sistema automático para extraer y monitorizar la evolución de aplicaciones presupuestarias de SICAL II a partir de capturas de pantalla.

## 📋 Características

- **Extracción automática de datos** mediante OCR (Reconocimiento Óptico de Caracteres)
- **Monitorización en tiempo real** de nuevas capturas de pantalla
- **Base de datos SQLite** para almacenamiento persistente
- **Dashboard interactivo** con visualización de evolución temporal
- **Exportación de datos** a CSV
- **Procesamiento automático** y organización de archivos

## 📊 Datos Extraídos

El sistema extrae automáticamente los siguientes campos de cada captura:

- Año de aplicación
- Código de concepto
- Descripción del concepto
- Saldo Inicial (Deudor/Acreedor)
- Total Haber
- Total Debe
- Propuestas de M/P (Mayor/Pago)
- Saldo Pendiente Acreedor
- Saldo Pendiente Deudor

## 🚀 Instalación

### Requisitos Previos

1. **Python 3.8 o superior**
2. **Tesseract OCR** instalado en el sistema:

   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install tesseract-ocr tesseract-ocr-spa

   # macOS
   brew install tesseract tesseract-lang

   # Windows
   # Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
   ```

### Instalación del Proyecto

1. Clonar el repositorio:
   ```bash
   git clone <repository-url>
   cd nopre-evolution
   ```

2. Crear un entorno virtual (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Uso

### 1. Monitorizar Capturas de Pantalla

Inicia el monitor que procesará automáticamente las capturas:

```bash
python run_monitor.py
```

El monitor:
- Observa la carpeta `screenshots/`
- Procesa automáticamente nuevas imágenes
- Extrae los datos mediante OCR
- Guarda los datos en la base de datos
- Mueve las imágenes procesadas a `processed/`

### 2. Visualizar el Dashboard

En otra terminal, inicia el dashboard:

```bash
python run_dashboard.py
```

O directamente con Streamlit:

```bash
streamlit run src/dashboard.py
```

El dashboard estará disponible en: `http://localhost:8501`

### 3. Añadir Capturas de Pantalla

Simplemente coloca tus capturas de pantalla (PNG, JPG, JPEG) en la carpeta `screenshots/`:

```bash
cp tu-captura.png screenshots/
```

El sistema las procesará automáticamente si el monitor está en ejecución.

## 📁 Estructura del Proyecto

```
nopre-evolution/
├── screenshots/          # Capturas de pantalla para procesar
├── processed/           # Capturas ya procesadas
├── data/               # Base de datos y exportaciones
│   └── sical_tracking.db
├── src/
│   ├── ocr_processor.py    # Módulo de procesamiento OCR
│   ├── database.py         # Gestión de base de datos
│   ├── monitor.py          # Monitor de archivos
│   └── dashboard.py        # Dashboard de visualización
├── run_monitor.py      # Script para ejecutar el monitor
├── run_dashboard.py    # Script para ejecutar el dashboard
├── requirements.txt    # Dependencias de Python
└── README.md          # Este archivo
```

## 🎯 Características del Dashboard

El dashboard ofrece múltiples visualizaciones:

1. **Métricas Clave**: Valores actuales de los principales indicadores
2. **Evolución Temporal**: Gráficos de línea mostrando cambios en el tiempo
3. **Comparativa**: Tabla comparando valores iniciales vs actuales
4. **Datos Detallados**: Tabla completa con todos los registros
5. **Capturas Procesadas**: Visualización de las imágenes originales

### Funcionalidades Adicionales

- Filtrado por concepto
- Descarga de datos en CSV
- Visualización de capturas procesadas
- Estadísticas generales

## 🔧 Uso Avanzado

### Procesamiento Manual

Si no quieres usar el monitor automático, puedes procesar archivos manualmente:

```python
from src.ocr_processor import SicalOCRProcessor
from src.database import SicalDatabase

processor = SicalOCRProcessor()
db = SicalDatabase()

# Procesar una imagen
data = processor.extract_data('ruta/a/imagen.png')

# Guardar en base de datos
if data:
    db.insert_data(data)
```

### Exportar Datos

```python
from src.database import SicalDatabase

db = SicalDatabase()

# Exportar todo a CSV
db.export_to_csv('data/export.csv')

# Obtener historial de un concepto
history = db.get_concept_history('30012')
```

### Consultar Base de Datos

```python
from src.database import SicalDatabase

db = SicalDatabase()

# Listar todos los conceptos
concepts = db.get_all_concepts()

# Obtener últimos datos
latest = db.get_latest_data()

# Historial completo
all_data = db.get_all_data()
```

## 🛠️ Solución de Problemas

### Tesseract no encontrado

**Error**: `TesseractNotFoundError`

**Solución**: Asegúrate de que Tesseract está instalado y en el PATH del sistema.

### Extracción de datos incorrecta

**Problema**: Los datos extraídos no son precisos

**Soluciones**:
- Asegúrate de que las capturas tienen buena calidad
- Las imágenes deben tener suficiente resolución
- Verifica que el idioma español está instalado en Tesseract

### El monitor no detecta nuevos archivos

**Problema**: Las imágenes no se procesan automáticamente

**Soluciones**:
- Verifica que el monitor está en ejecución
- Comprueba que las imágenes están en formato PNG, JPG o JPEG
- Revisa los logs para errores

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Notas

- El sistema está optimizado para el formato de SICAL II v4.2
- Los números se esperan en formato español (punto para miles, coma para decimales)
- Las capturas deben mostrar claramente los campos a extraer
- Se recomienda usar capturas en formato PNG para mejor calidad OCR

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 👤 Autor

Desarrollado para el seguimiento automatizado de aplicaciones presupuestarias en SICAL II.

---

**¿Necesitas ayuda?** Abre un issue en el repositorio.
