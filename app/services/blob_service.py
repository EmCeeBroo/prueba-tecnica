from azure.storage.blob import BlobServiceClient
from app.config import settings

class BlobService:
    def __init__(self):
        self.client = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
        self.container_name = settings.container_name
        # Crear contenedor si no existe
        try:
            self.client.create_container(name=self.container_name)
        except:
            pass  # ya existe

    async def upload(self, job_id: str, content: bytes):
        blob_client = self.client.get_blob_client(container=self.container_name, blob=f"{job_id}.csv")
        blob_client.upload_blob(content, overwrite=True)

    async def download(self, job_id: str) -> bytes:
        blob_client = self.client.get_blob_client(container=self.container_name, blob=f"{job_id}.csv")
        return blob_client.download_blob().readall()

    async def delete(self, job_id: str):
        blob_client = self.client.get_blob_client(container=self.container_name, blob=f"{job_id}.csv")
        blob_client.delete_blob()

storage = BlobService()