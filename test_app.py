import pytest
import httpx

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.anyio
async def test_login_exitoso():
    payload = {"usuario": "admin", "password": "password123"}
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

@pytest.mark.anyio
async def test_listar_productos():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/productos")
        assert response.status_code == 200
        data = response.json()
        assert "productos" in data
        assert "total" in data

@pytest.mark.anyio
async def test_reporte_ventas_exitoso():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/reporte-ventas")
        assert response.status_code == 200
        datos_respuesta = response.json()  # <-- Variable correcta sin la 's' final
        assert datos_respuesta["estado"] == "éxito"
        assert datos_respuesta["origen"] == "Fake Store API"
        assert "total_registros" in datos_respuesta