from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.storage import storage
from app.services.queue import queue
from app.services.database import db
from app.config import settings
from uuid import uuid4
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Subir archivo CSV para procesamiento"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos CSV")
    
    job_id = uuid4()
    content = await file.read()
    
    # Guardar archivo
    await storage.upload(str(job_id), content)
    
    # Crear job en BD
    await db.create_job(job_id)
    
    # Enviar mensaje a cola
    await queue.send(str(job_id))
    
    return {
        "job_id": str(job_id),
        "message": "Archivo recibido. El procesamiento comenzará en breve.",
        "status_url": f"/job/{job_id}"
    }

@router.get("/job/{job_id}")
async def get_job(job_id: str):
    """Consultar estado de un job"""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de job inválido")
    
    job = await db.get_job(job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    return {
        "job_id": str(job["id"]),
        "status": job["status"],
        "created_at": job["created_at"].isoformat() if job["created_at"] else None,
        "updated_at": job["updated_at"].isoformat() if job["updated_at"] else None,
        "error_message": job["error_message"]
    }

@router.get("/jobs/completed")
async def get_completed_jobs():
    """Endpoint para n8n - Obtener jobs completados"""
    jobs = await db.get_completed_jobs()
    return [dict(job) for job in jobs]

@router.get("/health")
async def health_check():
    """Verificar estado del servicio"""
    return {"status": "healthy", "mode": settings.mode}