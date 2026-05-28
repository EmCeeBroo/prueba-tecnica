import pytest

@pytest.fixture(scope="session")
def anyio_backend():
    """Configurar backend de asyncio para pruebas"""
    return "asyncio"