import aiosqlite

# El nombre del archivo que SQLite creará en tu disco duro
DB_NAME = "datos.db"

async def iniciar_db():
    # Abrimos la conexión (si el archivo no existe, SQLite lo crea mágicamente)
    async with aiosqlite.connect(DB_NAME) as db:
        # Le ordenamos crear la tabla 'productos' con sus columnas específicas
        await db.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                en_stock BOOLEAN NOT NULL
            )
        ''')
        # Confirmamos y guardamos los cambios en el disco duro
        await db.commit()
        print("Base de datos inicializada y lista.")