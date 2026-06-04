from app.config import settings

if settings.mode == "dev":
    from app.services.local_storage_service import LocalStorageService as StorageService
    from app.services.local_queue_service import LocalQueueService as QueueService
    print("🚀 Modo DEV: Usando almacenamiento local y cola en memoria")
else:
    from app.services.blob_service import BlobService as StorageService
    from app.services.queue_service import QueueService
    print("🐳 Modo DOCKER: Usando Azure Storage emulado")

from app.services.database import db

storage = StorageService()
queue = QueueService()