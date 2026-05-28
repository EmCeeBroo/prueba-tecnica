"""
Servicio de base de datos PostgreSQL
"""
import asyncpg
from app.config import settings
from uuid import UUID

class DatabaseService:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Establecer conexión a PostgreSQL"""
        self.pool = await asyncpg.create_pool(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            min_size=1,
            max_size=10
        )
        await self._create_tables()
        print("✅ Conexión a PostgreSQL establecida")
    
    async def _create_tables(self):
        """Crear tablas si no existen"""
        async with self.pool.acquire() as conn:
            # Tabla de ventas
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price NUMERIC(10,2) NOT NULL,
                    total NUMERIC(10,2) GENERATED ALWAYS AS (quantity * price) STORED
                )
            """)
            
            # Tabla de jobs (estado del procesamiento)
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {settings.job_table_name} (
                    id UUID PRIMARY KEY,
                    status VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP,
                    error_message TEXT
                )
            """)
            print("✅ Tablas creadas/verificadas")
    
    async def create_job(self, job_id: UUID):
        """Crear un nuevo job"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO {settings.job_table_name} (id, status) VALUES ($1, 'PENDING')",
                job_id
            )
    
    async def update_job_status(self, job_id: UUID, status: str, error_message: str = None):
        """Actualizar estado de un job"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"UPDATE {settings.job_table_name} SET status = $1, updated_at = NOW(), error_message = $2 WHERE id = $3",
                status, error_message, job_id
            )
    
    async def get_job(self, job_id: UUID):
        """Obtener información de un job"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                f"SELECT id, status, created_at, updated_at, error_message FROM {settings.job_table_name} WHERE id = $1",
                job_id
            )
    
    async def insert_sales_batch(self, batch):
        """Insertar lote de ventas"""
        if not batch:
            return
        async with self.pool.acquire() as conn:
            await conn.executemany(
                "INSERT INTO sales (date, product_id, quantity, price) VALUES ($1, $2, $3, $4)",
                batch
            )
            print(f"💾 Insertado lote de {len(batch)} registros")
    
    async def get_completed_jobs(self):
        """Obtener jobs completados (para n8n)"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                f"SELECT id, created_at, updated_at FROM {settings.job_table_name} WHERE status = 'COMPLETED' ORDER BY updated_at DESC LIMIT 100"
            )
    
    async def close(self):
        """Cerrar conexiones"""
        if self.pool:
            await self.pool.close()
            print("👋 Conexión a PostgreSQL cerrada")

# Instancia global
db = DatabaseService()