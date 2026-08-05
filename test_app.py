import pytest
import jwt
from httpx import AsyncClient, ASGITransport
from app import app, SECRET_KEY, ALGORITHM

# 1. Fixture para el cliente de pruebas de Falcon (ejecución asíncrona directa)
@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# 2. Generador de token JWT válido para rutas protegidas
@pytest.fixture
def token_valido():
    return jwt.encode({"sub": "admin", "rol": "admin"}, SECRET_KEY, algorithm=ALGORITHM)


# --- SUITE DE PRUEBAS COMPLETA ---

@pytest.mark.asyncio
async def test_login_exitoso(client):
    """Verifica el inicio de sesión correcto"""
    respuesta = await client.post("/login", json={
        "username": "admin",
        "password": "password123"
    })
    
    # Muestra respuesta en pantalla si falla
    if respuesta.status_code != 200:
        print("\n[DEBUG LOGIN]:", respuesta.text)
        
    assert respuesta.status_code == 200
    assert "token" in respuesta.json() or "access_token" in respuesta.json()


@pytest.mark.asyncio
async def test_crear_producto_sin_token(client):
    """Verifica el rechazo (401) cuando falta el Token JWT"""
    respuesta = await client.post("/productos", json={
        "nombre": "Mouse Gamer",
        "precio": 50.0,
        "stock": 5
    })
    assert respuesta.status_code == 401
    assert "error" in respuesta.json()


@pytest.mark.asyncio
async def test_crear_producto_datos_invalidos(client, token_valido):
    """Verifica el rechazo (400) mediante ProductoValidator"""
    headers = {"Authorization": f"Bearer {token_valido}"}
    payload_invalido = {
        "nombre": "",        # Nombre vacío (Inválido)
        "precio": -10,      # Precio negativo (Inválido)
        "stock": "muchos"   # Tipo de dato incorrecto (Inválido)
    }
    
    respuesta = await client.post("/productos", json=payload_invalido, headers=headers)
    assert respuesta.status_code == 400
    
    datos = respuesta.json()
    assert "detalles" in datos
    assert "nombre" in datos["detalles"]
    assert "precio" in datos["detalles"]


@pytest.mark.asyncio
async def test_listar_productos(client):
    """Verifica la consulta pública de productos (200)"""
    respuesta = await client.get("/productos")
    
    # Imprime la respuesta exacta si ocurre un error en PostgreSQL
    if respuesta.status_code != 200:
        print("\n--- DETALLE DEL ERROR AL LISTAR PRODUCTOS ---")
        print("Status Code:", respuesta.status_code)
        print("Cuerpo de la respuesta:", respuesta.text)
        print("---------------------------------------------\n")

    assert respuesta.status_code == 200
    assert "productos" in respuesta.json()