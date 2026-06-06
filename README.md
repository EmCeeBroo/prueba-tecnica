🐳 Dockerized Application

# LogyCA Sales Processor

Asynchronous system for processing large CSV sales files containing millions of records.

The system uploads the file, stores it in **Azure Blob Storage (or local storage)**, queues the job, and a background worker processes it asynchronously, inserting data into **PostgreSQL** in batches to avoid database overload.

It also includes an **n8n workflow** that calculates daily sales totals and stores aggregated results.

## 🧱 Architecture

* **FastAPI** – Endpoints:

  * `POST /upload` – Upload a CSV file and receive a `job_id`
  * `GET /job/{job_id}` – Check processing status
  * `GET /jobs/completed` – List completed jobs (used by n8n)
  * `GET /health` – Health check endpoint

* **Worker** – Infinite loop that consumes messages from a shared queue (PostgreSQL), processes CSV files line by line without loading the entire file into memory, and inserts records in batches.

* **PostgreSQL** – Tables:

  * `sales` (sales records with an automatically generated `total` field)
  * `jobs` (processing status tracking)
  * `job_queue` (shared queue between API and worker)
  * `sales_daily_summary` (daily summary used by n8n)

* **Storage** – Local storage (`dev` mode) or Azure Blob Storage (`docker` mode using Azurite).

* **Queue** – During development, an in-memory `deque` can be used. For production-grade reliability, a PostgreSQL-based queue was implemented using `FOR UPDATE SKIP LOCKED` transactions.

* **n8n** – External orchestrator that runs a scheduled workflow: retrieves completed jobs, calculates daily sales totals, and stores results in `sales_daily_summary`.

## 📌 Key Technical Decisions

| Decision                                     | Implementation                                                                                         |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Avoid loading the entire CSV into memory     | `csv.reader` with `StringIO`, processing row by row                                                    |
| Bulk inserts without overwhelming PostgreSQL | Batches of 5000 records + `asyncio.sleep(0.05)` between batches                                        |
| Shared queue between API and Worker          | `job_queue` table using `FOR UPDATE SKIP LOCKED` transactions                                          |
| Execution modes                              | `dev` (local storage, in-memory queue) and `docker` (Azure Blob + Queue emulated with Azurite)         |
| Error handling                               | Invalid rows are logged and processing continues; job status changes to `FAILED` with an error message |
| Unit testing                                 | `pytest` with mocks to isolate external services                                                       |

## 🔧 Prerequisites

### Local Mode (Development)

* Python 3.12 (or 3.11)
* Local PostgreSQL instance running
* Optional: Postman or `curl` for API testing

### Docker Mode (Local Production Environment)

* Docker Desktop installed
* No need for local PostgreSQL or Python installation

## 🐳 Basic Docker Commands (Beginner Friendly)

If you are new to Docker, don't worry. Here is a quick reference for the commands used in this project:

| Command                                                         | Description                                                                                                                    |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `docker-compose up -d --build`                                  | Starts all containers (PostgreSQL, Azurite, API, Worker, n8n) in detached mode. `--build` rebuilds images if code has changed. |
| `docker ps`                                                     | Displays all currently running containers.                                                                                     |
| `docker-compose logs -f api`                                    | Shows real-time logs for the API service. Replace `api` with `worker` or `n8n` to inspect other services.                      |
| `docker-compose logs -f`                                        | Displays logs from all services simultaneously.                                                                                |
| `docker-compose down`                                           | Stops and removes all containers while preserving persistent data.                                                             |
| `docker-compose down -v`                                        | Stops containers and removes associated volumes (PostgreSQL, n8n data, etc.). Use when starting from scratch.                  |
| `docker exec -it logyca_postgres psql -U postgres -d logyca_db` | Opens an interactive PostgreSQL terminal inside the container.                                                                 |

> **Tip:** If you prefer a graphical interface, install the Docker extension in VS Code (whale icon) to manage containers visually.

## 📌 n8n Reminder

> **Note for n8n beginners:**
> Once you publish a workflow using the **Publish** button, n8n will execute it automatically according to the schedule you configured (for example, every day at midnight).
>
> You do not need to keep your browser open or manually click **Execute Workflow** again.
>
> As long as the Docker containers are running (`docker-compose up -d`), n8n will continue executing workflows automatically.
>
> You can safely shut down and restart your computer. When Docker starts again, n8n will restore its workflows and continue operating normally.

## 📦 Installation and Execution

### 🔹 Local Mode (Development)

```bash
# Clone repository
git clone <repository-url>
cd logyca_sales_processor

# Create virtual environment
python -m venv venv

# Activate virtual environment

# Linux / macOS
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Configure .env file (see .env.example)
# Minimum example for development mode:
#
# mode=dev
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=logyca_db
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your_password
# UPLOAD_DIR=./uploads

# Create database if it does not exist
createdb logyca_db

# Or create it manually using pgAdmin

# Terminal 1: Start worker
python -m app.workers.processor

# Terminal 2: Start API
uvicorn app.main:app --reload
```
