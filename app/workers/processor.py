import asyncio
import csv
from io import StringIO
from app.services.storage import storage
from app.services.queue import queue
from app.services.database import db
from app.config import settings
from uuid import UUID

async def process_csv_in_chunks(job_id: str, batch_size: int = 5000):
    """Procesa CSV línea por línea, inserta en lotes sin cargar todo en memoria"""
    content = await storage.download(job_id)
    # Usar StringIO para simular un archivo en memoria
    csv_text = content.decode('utf-8')
    reader = csv.reader(StringIO(csv_text))
    headers = next(reader)  # saltar cabecera
    batch = []
    for row_num, row in enumerate(reader, start=2):
        # Validar formato básico
        if len(row) != 4:
            raise ValueError(f"Fila {row_num}: se esperaban 4 columnas, se obtuvieron {len(row)}")
        date, product_id, quantity, price = row
        batch.append((
            date,
            int(product_id),
            int(quantity),
            float(price)
        ))
        if len(batch) >= batch_size:
            await db.insert_sales_batch(batch)
            batch = []
            # Pequeña pausa para no saturar PostgreSQL
            await asyncio.sleep(0.05)
    if batch:
        await db.insert_sales_batch(batch)

async def worker_loop():
    await db.connect()
    print("🚀 Worker iniciado. Esperando jobs...")
    print(f"📁 Modo: {settings.mode}")
    print(f"💾 Directorio uploads: {settings.upload_dir}")
    print(f"🗄️ Base de datos: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    print("=" * 50)
    
    while True:
        messages = await queue.receive(max_messages=5)
        for msg in messages:
            job_id = msg["job_id"]
            print(f"\n📥 Procesando job {job_id}")
            try:
                await db.update_job_status(UUID(job_id), "PROCESSING")
                await process_csv_in_chunks(job_id)
                await db.update_job_status(UUID(job_id), "COMPLETED")
                await queue.delete(msg["id"], msg["pop_receipt"])
                print(f"✅ Job {job_id} completado")
            except Exception as e:
                print(f"❌ Error en job {job_id}: {e}")
                await db.update_job_status(UUID(job_id), "FAILED", str(e))
                # En una cola real, aquí podrías no borrar para reintentar
                await queue.delete(msg["id"], msg["pop_receipt"])
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        print("\n👋 Worker detenido por el usuario")