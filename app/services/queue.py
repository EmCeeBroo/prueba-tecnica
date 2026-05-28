"""
Servicio de cola usando PostgreSQL (compartida entre procesos)
"""
from app.services.database import db

class QueueService:
    async def send(self, job_id: str):
        """Enviar mensaje a la cola (guardar en BD)"""
        async with db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO job_queue (job_id, status, created_at) 
                VALUES ($1, 'pending', NOW())
            """, job_id)
        print(f"📨 Mensaje enviado a cola: job {job_id}")
    
    async def receive(self, max_messages: int = 10):
        """Recibir mensajes pendientes de la cola"""
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch("""
                    SELECT id, job_id 
                    FROM job_queue 
                    WHERE status = 'pending' 
                    ORDER BY created_at 
                    LIMIT $1
                    FOR UPDATE SKIP LOCKED
                """, max_messages)
                
                messages = []
                for row in rows:
                    await conn.execute("""
                        UPDATE job_queue 
                        SET status = 'processing', updated_at = NOW() 
                        WHERE id = $1
                    """, row["id"])
                    messages.append({
                        "id": str(row["id"]),
                        "job_id": row["job_id"],
                        "pop_receipt": str(row["id"])
                    })
                if messages:
                    print(f"📬 Recibidos {len(messages)} mensajes de la cola")
                return messages
    
    async def delete(self, message_id: str, pop_receipt: str):
        """Eliminar mensaje procesado"""
        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM job_queue WHERE id = $1", int(message_id))
            print(f"🗑️ Mensaje {message_id} eliminado de la cola")

queue = QueueService()