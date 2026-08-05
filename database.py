import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

# Usamos el nombre del servicio 'db' configurado en Docker Compose
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin_db:password_seguro@db:5432/inventario_db")
# database.py

async def listar_productos(conexion, limit: int = 10, offset: int = 0):
    """
    Consulta a la base de datos aplicando paginación.
    $1 es el límite (cuántos traer) y $2 es el desplazamiento (cuántos saltar).
    """
    query = """
        SELECT * FROM productos
        LIMIT $1 OFFSET $2;
    """
    
    # Se inyectan las variables de forma segura
    registros = await conexion.fetch(query, limit, offset)
    
    # Se retorna una lista de diccionarios
    return [dict(registro) for registro in registros]
    