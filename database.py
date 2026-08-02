import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

# Usamos el nombre del servicio 'db' configurado en Docker Compose
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin_db:password_seguro@db:5432/inventario_db")

async def iniciar_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL,
            precio REAL NOT NULL,
            en_stock BOOLEAN NOT NULL
        )
    ''')
    await conn.close()
    