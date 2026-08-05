import json
import httpx
import jwt
import asyncpg
import falcon
from falcon.asgi import App

# Módulos locales del proyecto
from docs import obtener_esquema_openapi
from middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from database import listar_productos, DATABASE_URL
from validators import ProductoValidator

# Llave secreta para firmar los tokens JWT (mínimo 32 caracteres para seguridad)
SECRET_KEY = "super-secreto-seguro-de-daniel-2024-v1"
ALGORITHM = "HS256"


# 1. Recurso de Autenticación (Login)
class LoginResource:
    async def on_post(self, req, resp):
        try:
            raw_body = await req.bounded_stream.read()
            data = json.loads(raw_body.decode('utf-8'))

            # Validación flexible de llaves
            usuario = data.get("username") or data.get("usuario")
            password = data.get("password") or data.get("contrasena")

            if usuario == "admin" and password == "password123":
                payload = {"sub": usuario, "rol": "admin"}
                token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

                resp.status = falcon.HTTP_200
                resp.text = json.dumps({
                    "mensaje": "Autenticación exitosa",
                    "access_token": token,
                    "token": token,
                    "tipo": "Bearer"
                })
            else:
                resp.status = falcon.HTTP_401
                resp.text = json.dumps({"error": "Credenciales inválidas"})

        except Exception as e:
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({"error": "Petición JSON inválida", "detalle": str(e)})


# 2. Recurso de Productos
class ProductosResource:
    async def on_post(self, req, resp):
        try:
            # Validación de Token JWT
            auth_header = req.get_header("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                resp.status = falcon.HTTP_401
                resp.text = json.dumps({"error": "Acceso denegado. Falta el Token JWT"})
                return

            token = auth_header.split(" ")[1]
            try:
                jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            except jwt.PyJWTError:
                resp.status = falcon.HTTP_401
                resp.text = json.dumps({"error": "Token inválido o expirado"})
                return

            # Lectura del cuerpo de la petición
            raw_body = await req.bounded_stream.read()
            data = json.loads(raw_body.decode('utf-8'))

            # 🛡️ Validación de datos con validators.py
            errores = ProductoValidator.validar_creacion(data)
            if errores:
                resp.status = falcon.HTTP_400
                resp.text = json.dumps({
                    "error": "Falló la validación de los datos de entrada.",
                    "detalles": errores
                })
                return

            # Conexión e inserción en PostgreSQL
            try:
                conn = await asyncpg.connect(DATABASE_URL)
                await conn.execute(
                    "INSERT INTO productos (nombre, precio, en_stock) VALUES ($1, $2, $3)",
                    data.get("nombre"),
                    float(data.get("precio")),
                    bool(data.get("stock", True))
                )
                await conn.close()
            except ValueError as ve:
                resp.status = falcon.HTTP_400
                resp.text = json.dumps({"error": "Tipo de dato inválido", "detalle": str(ve)})
                return
            except Exception as db_error:
                resp.status = falcon.HTTP_500
                resp.text = json.dumps({"error": "Error en base de datos", "detalle": str(db_error)})
                return

            # Respuesta exitosa
            resp.status = falcon.HTTP_201
            resp.text = json.dumps({
                "mensaje": "Producto guardado en PostgreSQL (Docker)",
                "producto": data
            })

        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": "Error interno del servidor", "detalle": str(e)})

    async def on_get(self, req, resp):
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            
            # Garantiza la existencia de la tabla en PostgreSQL
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    precio NUMERIC(10, 2) NOT NULL,
                    en_stock BOOLEAN DEFAULT TRUE
                );
            """)

            # Consulta de registros
            filas = await conn.fetch("SELECT id, nombre, precio, en_stock FROM productos")
            await conn.close()

            lista_productos = []
            for fila in filas:
                lista_productos.append({
                    "id": fila["id"],
                    "nombre": fila["nombre"],
                    "precio": float(fila["precio"]),
                    "en_stock": bool(fila["en_stock"])
                })

            resp.status = falcon.HTTP_200
            resp.text = json.dumps({
                "total": len(lista_productos),
                "productos": lista_productos
            })
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": "Error al consultar productos", "detalle": str(e)})


# 3. Inicialización de la Aplicación Falcon ASGI
app = App(middleware=[
    RateLimitMiddleware(),
    SecurityHeadersMiddleware()
])

# Instancias de recursos
login_resource = LoginResource()
productos_resource = ProductosResource()

# Rutas de la API
app.add_route("/login", login_resource)
app.add_route("/productos", productos_resource)