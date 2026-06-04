🐳 Docker ready

# LogyCA Sales Processor

Sistema asíncrono para procesar archivos CSV de ventas de millones de registros.  
Sube el archivo, lo guarda en **Azure Blob Storage (o local)**, encola el trabajo y un worker lo procesa en segundo plano insertando en **PostgreSQL** por lotes para no saturar la base de datos.  
Incluye un workflow en **n8n** que calcula ventas por día y guarda un resumen.

## 🧱 Arquitectura

- **FastAPI** – Endpoints:
  - `POST /upload` – subir CSV, recibe `job_id`
  - `GET /job/{job_id}` – consultar estado
  - `GET /jobs/completed` – listar jobs terminados (para n8n)
  - `GET /health` – health check
- **Worker** – Bucle infinito que consume mensajes de una cola compartida (PostgreSQL), procesa CSV línea por línea sin cargar todo en memoria e inserta en lotes.
- **PostgreSQL** – Tablas:
  - `sales` (ventas, con campo `total` generado automáticamente)
  - `jobs` (estado del procesamiento)
  - `job_queue` (cola compartida entre API y worker)
  - `sales_daily_summary` (resumen diario usado por n8n)
- **Almacenamiento** – Local (modo `dev`) o Azure Blob Storage (modo `docker` con Azurite).
- **Cola** – En desarrollo se usa `deque` en memoria, pero para robustez se implementó una cola basada en PostgreSQL con transacciones `FOR UPDATE SKIP LOCKED`.
- **n8n** – Orquestador externo que ejecuta un workflow diario: consulta jobs completados, calcula ventas por día y guarda en `sales_daily_summary`.

## 📌 Decisiones técnicas clave

| Decisión | Cómo se implementó |
|----------|-------------------|
| No cargar CSV completo en memoria | `csv.reader` sobre `StringIO` y procesar fila a fila |
| Inserción masiva sin saturar DB | Lotes de 5000 registros + `asyncio.sleep(0.05)` entre lotes |
| Cola compartida entre API y Worker | Tabla `job_queue` con transacciones `FOR UPDATE SKIP LOCKED` |
| Modos de ejecución | `dev` (almacenamiento local, cola en memoria) y `docker` (Azure Blob+Queue emulados con Azurite) |
| Manejo de errores | Si falla una fila se registra y continúa; el estado del job pasa a `FAILED` con mensaje |
| Pruebas unitarias | `pytest` con mocks para aislar servicios externos |

## 🔧 Requisitos previos

### Modo local (desarrollo)
- Python 3.12 (o 3.11) instalado
- PostgreSQL local corriendo
- Opcional: `curl` o Postman para probar la API

### Modo Docker (producción local)
- Docker Desktop instalado
- No necesitas PostgreSQL ni Python local

### 🐳 Comandos básicos de Docker (para principiantes)

Si nunca has usado Docker, no te preocupes. Aquí tienes una mini guía de los comandos que usamos en este proyecto:

| Comando | ¿Qué hace? |
|---------|-------------|
| `docker-compose up -d --build` | Levanta todos los contenedores (PostgreSQL, Azurite, API, Worker, n8n) en segundo plano (`-d`). `--build` reconstruye las imágenes si cambió el código. |
| `docker ps` | Muestra los contenedores que están corriendo en este momento. |
| `docker-compose logs -f api` | Muestra los logs (bitácora) de la API en tiempo real (como tener una terminal abierta). Cambia `api` por `worker` o `n8n` para ver otros servicios. |
| `docker-compose logs -f` | Muestra los logs de **todos** los servicios a la vez. |
| `docker-compose down` | Detiene y elimina todos los contenedores (pero no borra los datos de las bases de datos). |
| `docker-compose down -v` | Detiene los contenedores **y borra los volúmenes** (datos de PostgreSQL, n8n, etc.). Úsalo si quieres empezar de cero. |
| `docker exec -it logyca_postgres psql -U postgres -d logyca_db` | Entra a la terminal interactiva de PostgreSQL dentro del contenedor para ejecutar consultas SQL directamente. |

> **Tip:** Si no quieres recordar todos los comandos, puedes usar la extensión **Docker** en VS Code (icono de ballena) para ver y manejar los contenedores con clics.

### Para recordar en 8n8

> **Nota para principiantes en n8n:**  
> Una vez que publiques el workflow (botón "Publish"), n8n lo ejecutará automáticamente según la programación que definiste (por ejemplo, cada día a medianoche). No necesitas mantener el navegador abierto ni volver a hacer clic en "Execute workflow". Mientras los contenedores de Docker estén corriendo (`docker-compose up -d`), n8n funcionará solo. Puedes apagar y prender tu PC; al volver a levantar Docker, n8n recordará el workflow y seguirá ejecutándose.

## 📦 Instalación y ejecución

### 🔹 Modo local (desarrollo)

```bash
# Clonar repositorio
git clone <url-del-repo>
cd logyca_sales_processor

# Crear entorno virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
# o venv\Scripts\activate   Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar archivo .env (ver .env.example)
# Ejemplo mínimo para modo dev:
#   mode=dev
#   POSTGRES_HOST=localhost
#   POSTGRES_PORT=5432
#   POSTGRES_DB=logyca_db
#   POSTGRES_USER=postgres
#   POSTGRES_PASSWORD=tu_contraseña
#   UPLOAD_DIR=./uploads

# Crear la base de datos (si no existe)
createdb logyca_db   # o desde pgAdmin

# En una terminal: iniciar el worker
python -m app.workers.processor

# En otra terminal: iniciar la API
uvicorn app.main:app --reload
