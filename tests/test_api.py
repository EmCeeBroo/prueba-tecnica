import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from app.main import app

@pytest.mark.asyncio
async def test_health():
    """Probar endpoint /health"""
    # Usar transporte ASGI para conectar con FastAPI
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["mode"] == "dev"

@pytest.mark.asyncio
async def test_upload_csv_success():
    """Probar subida exitosa de CSV"""
    mock_content = b"date,product_id,quantity,price\n2026-01-01,1001,2,10.5"
    files = {"file": ("test.csv", mock_content, "text/csv")}
    
    with patch("app.api.endpoints.storage.upload", new_callable=AsyncMock) as mock_storage, \
         patch("app.api.endpoints.db.create_job", new_callable=AsyncMock) as mock_create_job, \
         patch("app.api.endpoints.queue.send", new_callable=AsyncMock) as mock_queue:
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["message"] == "Archivo recibido. El procesamiento comenzará en breve."
        
        # Verificar que se llamaron los mocks
        mock_storage.assert_awaited_once()
        mock_create_job.assert_awaited_once()
        mock_queue.assert_awaited_once()

@pytest.mark.asyncio
async def test_upload_invalid_file_type():
    """Probar subida de archivo que no es CSV"""
    files = {"file": ("test.txt", b"content", "text/plain")}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "Solo se permiten archivos CSV" in response.text

@pytest.mark.asyncio
async def test_get_job_not_found():
    """Probar consulta de job que no existe"""
    random_id = str(uuid4())

    #Mockear db:get_job para que devuelva None (job no encontrado)
    with patch("app.api.endpoints.db.get_job", new_callable=AsyncMock) as mock_get_job:
        mock_get_job.return_value = None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/job/{random_id}")
    
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_job_success():
    """Probar consulta de job existente"""
    from datetime import datetime
    
    job_id = uuid4()
    mock_job = {
        "id": job_id,
        "status": "COMPLETED",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "error_message": None
    }
    
    with patch("app.api.endpoints.db.get_job", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_job
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/job/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(job_id)
        assert data["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_get_completed_jobs():
    """Probar listado de jobs completados"""
    with patch("app.api.endpoints.db.get_completed_jobs", new_callable=AsyncMock) as mock_completed:
        mock_completed.return_value = []
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/jobs/completed")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)