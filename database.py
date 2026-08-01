import asyncpg

# Credenciales de conexión al contenedor Docker de PostgreSQL
DATABASE_URL = "postgresql://admin_db:password_seguro@localhost:5432/inventario_db"

async def iniciar_db():
    # Nos conectamos al servidor de PostgreSQL
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Creamos la tabla de productos si no existe
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL,
            precio REAL NOT NULL,
            en_stock BOOLEAN NOT NULL
        )
    ''')
    
    # Cerramos la conexión de arranque
    await conn.close()
    print("Conexión exitosa y tabla creada en PostgreSQL (Docker).")


    