# LogyCA Sales Processor

## Descripción
Sistema asíncrono para procesar archivos CSV de ventas de millones de registros.  
Sube el archivo, lo guarda en disco local, encola el trabajo y un worker lo procesa en segundo plano insertando en PostgreSQL por lotes para no saturar la base de datos.

## Arquitectura
- **FastAPI**: Endpoints `/upload` y `/job/{job_id}`
- **Worker**: Bucle infinito que monitorea cola local (archivos JSON), procesa CSV línea por línea sin cargar todo en memoria.
- **PostgreSQL**: Tabla `sales` con columna calculada `total` y tabla `jobs` para estado.
- **Almacenamiento local** (simula Azure Blob) y **cola local** (simula Azure Queue) - fácilmente reemplazables por servicios cloud.

## Decisiones técnicas
- **No cargar CSV completo en memoria**: Se usa `csv.reader` sobre `StringIO` y se procesa fila a fila.
- **Inserción masiva**: Se acumulan lotes de 5000 filas y se insertan con `executemany`.
- **Evitar saturar PostgreSQL**: Pequeño `asyncio.sleep(0.05)` entre lotes y uso de connection pool.
- **Manejo de errores**: Si falla una fila, se revierte el lote? En esta versión, se falla todo el job y se guarda error. Para producción se podría implementar skip de filas malas.

## Requisitos previos
- Python 3.10+
- PostgreSQL local instalado y corriendo
- Crear la base de datos: `createdb logyca_db`

## Instalación y ejecución
```bash
# Clonar
git clone <tu-repo>
cd logyca_sales_processor

# Crear entorno virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
# o venv\Scripts\activate   Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env con tu contraseña de PostgreSQL

# En una terminal, ejecutar el worker
python app/workers/processor.py

# En otra terminal, ejecutar la API
uvicorn app.main:app --reload