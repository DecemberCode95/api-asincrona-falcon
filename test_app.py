import pytest
from falcon import testing
from app import app

@pytest.fixture
def client():
    # Creamos el navegador fantasma
    return testing.TestClient(app)

# 1. Quitamos la etiqueta asíncrona y la palabra 'async'
def test_reporte_ventas_exitoso(client):
    
    # 2. Quitamos el 'await'. Falcon maneja la asincronía internamente por nosotros
    response = client.simulate_get('/reporte-ventas')
    
    # Verificaciones
    assert response.status_code == 200
    
    datos_respuesta = response.json
    
    assert datos_respuesta["estado"] == "éxito"
    assert datos_respuesta["origen"] == "Fake Store API"
    assert "total_registros" in datos_respuesta
    assert "datos" in datos_respuesta