import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import patch
import asyncio

@pytest.mark.asyncio
async def test_upload_and_job_status():
    # Mock de los servicios para no escribir archivos ni BD real
    with patch("app.api.endpoints.storage.upload") as mock_upload, \
         patch("app.api.endpoints.db.create_job") as mock_create_job, \
         patch("app.api.endpoints.queue.send") as mock_queue:
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            csv_content = b"date,product_id,quantity,price\n2026-01-01,1001,2,10.5"
            response = await client.post("/upload", files={"file": ("test.csv", csv_content)})
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        
        # Simular que get_job devuelve un job
        job_id = data["job_id"]
        with patch("app.api.endpoints.db.get_job") as mock_get_job:
            from app.models.job import JobStatus
            from uuid import UUID
            from datetime import datetime
            fake_job = {
                "id": UUID(job_id),
                "status": JobStatus.PENDING,
                "created_at": datetime.now(),
                "updated_at": None,
                "error_message": None
            }
            mock_get_job.return_value = fake_job
            response2 = await client.get(f"/job/{job_id}")
        assert response2.status_code == 200
        assert response2.json()["status"] == "PENDING"