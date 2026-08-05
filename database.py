from typing import List, Dict, Any
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

# Usamos el nombre del servicio 'db' configurado en Docker Compose
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin_db:password_seguro@db:5432/inventario_db"
)


async def listar_productos(
    conexion: asyncpg.Connection, 
    limit: int = 10, 
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Consulta a la base de datos aplicando paginación.
    
    Args:
        conexion: Conexión asyncpg a la BD
        limit: Número máximo de productos a retornar
        offset: Desplazamiento (cuántos productos saltar)
        
    Returns:
        Lista de diccionarios con los productos
    """
    query: str = """
        SELECT * FROM productos
        LIMIT $1 OFFSET $2;
    """
    
    # Se inyectan las variables de forma segura
    registros: List[asyncpg.Record] = await conexion.fetch(query, limit, offset)
    
    # Se retorna una lista de diccionarios
    return [dict(registro) for registro in registros]
