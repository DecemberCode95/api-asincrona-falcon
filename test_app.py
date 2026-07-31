# 1. Nativas (No hay en este caso)
# 2. Terceros
import pytest
import falcon.asgi
from falcon import testing
# 3. Locales
from app import app

@pytest.fixture
def client():
    # Prepara un cliente falso para golpear tu API
    return testing.TestClient(app)

@pytest.mark.asyncio
async def test_reporte_ventas_exitoso(client):
    # Ejecuta
    response = await client.simulate_get('/reporte-ventas')
    # Valida
    assert response.status_code == 200
    assert response.json["estado"] == "éxito"