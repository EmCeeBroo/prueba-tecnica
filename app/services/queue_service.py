from azure.storage.queue import QueueServiceClient
import json
from app.config import settings

class QueueService:
    def __init__(self):
        self.client = QueueServiceClient.from_connection_string(settings.azure_storage_connection_string)
        self.queue_name = settings.queue_name
        # Crear cola si no existe
        self.queue_client = self.client.get_queue_client(self.queue_name)
        try:
            self.queue_client.create_queue()
        except:
            pass

    async def send(self, job_id: str):
        message = json.dumps({"job_id": job_id})
        self.queue_client.send_message(message)

    async def receive(self, max_messages=10):
        messages = self.queue_client.receive_messages(max_messages=max_messages, visibility_timeout=30)
        result = []
        for msg in messages:
            data = json.loads(msg.content)
            result.append({
                "id": msg.id,
                "job_id": data["job_id"],
                "pop_receipt": msg.pop_receipt
            })
        return result

    async def delete(self, message_id, pop_receipt):
        self.queue_client.delete_message(message_id, pop_receipt)

queue = QueueService()