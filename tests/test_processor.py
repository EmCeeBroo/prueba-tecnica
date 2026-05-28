import pytest
import asyncio
from app.workers.processor import process_csv_in_chunks
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_process_csv_in_chunks():
    # Simular CSV pequeño
    csv_content = b"date,product_id,quantity,price\n2026-01-01,1001,2,10.5\n2026-01-02,1002,1,5.2"
    
    with patch("app.workers.processor.storage.download", AsyncMock(return_value=csv_content)), \
         patch("app.workers.processor.db.insert_sales_batch") as mock_insert:
        
        await process_csv_in_chunks("test-job", batch_size=1)  # batch pequeño
        # Verificar que se llamó a insert_sales_batch dos veces (una por cada fila)
        assert mock_insert.call_count == 2