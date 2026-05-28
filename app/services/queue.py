"""
Servicio de cola en memoria (reemplaza Azure Queue en modo dev)
"""
from collections import deque

class QueueService:
    def __init__(self):
        self.queue = deque()
        self.counter = 0
    
    async def send(self, job_id: str):
        """Enviar mensaje a la cola"""
        message = {
            "id": str(self.counter),
            "job_id": job_id,
            "pop_receipt": str(self.counter)
        }
        self.queue.append(message)
        self.counter += 1
        print(f"📨 Mensaje enviado: job {job_id}")
        return message
    
    async def receive(self, max_messages: int = 10):
        """Recibir mensajes de la cola"""
        messages = []
        for _ in range(min(max_messages, len(self.queue))):
            msg = self.queue.popleft()
            messages.append(msg)
        if messages:
            print(f"📬 Recibidos {len(messages)} mensajes")
        return messages
    
    async def delete(self, message_id: str, pop_receipt: str):
        """Eliminar mensaje (en memoria no es necesario, pero mantenemos la interfaz)"""
        # En memoria, los mensajes ya se eliminaron al recibirlos con .popleft()
        pass
    
    async def size(self):
        """Obtener tamaño de la cola"""
        return len(self.queue)

# Instancia global
queue = QueueService()