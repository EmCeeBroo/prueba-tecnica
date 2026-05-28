import asyncio
import csv
from io import StringIO
from datetime import datetime
from app.services.storage import storage
from app.services.queue import queue
from app.services.database import db
from app.config import settings
from uuid import UUID

async def process_csv_in_chunks(job_id: str, batch_size: int = 5000):
    """Procesa CSV línea por línea, inserta en lotes sin cargar todo en memoria"""
    content = await storage.download(job_id)
    csv_text = content.decode('utf-8')
    reader = csv.reader(StringIO(csv_text))
    next(reader)  # saltar cabecera
    batch = []
    row_count = 0
    
    for row_num, row in enumerate(reader, start=2):
        if len(row) != 4:
            raise ValueError(f"Fila {row_num}: se esperaban 4 columnas, se obtuvieron {len(row)}")
        
        date_str, product_id, quantity, price = row
        
        # 👇 CONVERTIR TIPOS CORRECTAMENTE 👇
        try:
            # Convertir fecha: string → objeto date
            date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            
            # Convertir números
            product_id_int = int(product_id.strip())
            quantity_int = int(quantity.strip())
            price_float = float(price.strip())
            
            batch.append((
                date_obj,           # date (objeto date, no string)
                product_id_int,     # integer
                quantity_int,       # integer
                price_float         # numeric/decimal
            ))
            row_count += 1
            
        except ValueError as e:
            print(f"⚠️ Error en fila {row_num}: {e} - Datos: {row}")
            continue
        
        if len(batch) >= batch_size:
            await db.insert_sales_batch(batch)
            print(f"💾 Insertado lote de {len(batch)} registros (total: {row_count})")
            batch = []
            await asyncio.sleep(0.05)
    
    if batch:
        await db.insert_sales_batch(batch)
        print(f"💾 Insertado último lote de {len(batch)} registros")
    
    print(f"✅ Procesamiento completado. Total de registros válidos: {row_count}")
    return row_count

async def worker_loop():
    await db.connect()
    print("=" * 50)
    print("🚀 WORKER INICIADO")
    print(f"📁 Modo: {settings.mode}")
    print(f"💾 Directorio uploads: {settings.upload_dir}")
    print(f"🗄️ Base de datos: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    print("=" * 50)
    print("⏳ Esperando mensajes en la cola...")
    
    while True:
        messages = await queue.receive(max_messages=5)
        for msg in messages:
            job_id_raw = msg["job_id"]
            job_id_str = str(job_id_raw)
            print(f"\n📥 Procesando job {job_id_str}")
            try:
                await db.update_job_status(UUID(job_id_str), "PROCESSING")
                await process_csv_in_chunks(job_id_str)
                await db.update_job_status(UUID(job_id_str), "COMPLETED")
                await queue.delete(msg["id"], msg["pop_receipt"])
                print(f"✅ Job {job_id_str} COMPLETADO")
            except Exception as e:
                print(f"❌ Error en job {job_id_str}: {e}")
                import traceback
                traceback.print_exc()
                await db.update_job_status(UUID(job_id_str), "FAILED", str(e))
                await queue.delete(msg["id"], msg["pop_receipt"])
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        print("\n👋 Worker detenido por el usuario")