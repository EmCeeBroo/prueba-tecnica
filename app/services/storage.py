"""
Servicio de almacenamiento local (reemplaza Azure Blob en modo dev)
"""
import os
import aiofiles
from app.config import settings

class StorageService:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        # Asegurar que el directorio existe
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def upload(self, job_id: str, file_content: bytes):
        """Guardar archivo en sistema local"""
        file_path = os.path.join(self.upload_dir, f"{job_id}.csv")
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        print(f"💾 Archivo guardado: {file_path}")
        return file_path
    
    async def download(self, job_id: str) -> bytes:
        """Leer archivo del sistema local"""
        file_path = os.path.join(self.upload_dir, f"{job_id}.csv")
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()
    
    async def delete(self, job_id: str):
        """Eliminar archivo"""
        file_path = os.path.join(self.upload_dir, f"{job_id}.csv")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Archivo eliminado: {file_path}")

# Instancia global para usar en toda la app
storage = StorageService()