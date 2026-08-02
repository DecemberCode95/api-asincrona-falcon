import json
import httpx
import jwt
import asyncpg
from middleware import RateLimitMiddleware
import json
import falcon
from docs import obtener_esquema_openapi
from falcon.asgi import App
from pydantic import ValidationError

from database import iniciar_db, DATABASE_URL
from models import ProductoSchema, LoginSchema

# Llave secreta para firmar los tokens JWT
SECRET_KEY = "super-secreto-seguro-de-daniel"
ALGORITHM = "HS256"

# 1. Recurso de Autenticación
class LoginResource:
    async def on_post(self, req, resp):
        try:
            raw_body = await req.bounded_stream.read()
            data = json.loads(raw_body.decode('utf-8'))
            credenciales = LoginSchema(**data)

            if credenciales.usuario == "admin" and credenciales.password == "password123":
                payload = {"sub": credenciales.usuario, "rol": "administrador"}
                token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

                resp.status = 200
                resp.text = json.dumps({
                    "mensaje": "Autenticación exitosa",
                    "access_token": token,
                    "tipo": "Bearer"
                })
            else:
                resp.status = 401
                resp.text = json.dumps({"error": "Credenciales inválidas"})

        except Exception as e:
            resp.status = 400
            resp.text = json.dumps({"error": "Formato incorrecto", "detalle": str(e)})

# 2. Recurso de Productos
class ProductosResource:
    async def on_post(self, req, resp):
        try:
            auth_header = req.get_header("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                resp.status = 401
                resp.text = json.dumps({"error": "Acceso denegado. Falta el Token JWT"})
                return

            token = auth_header.split(" ")[1]
            try:
                jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            except jwt.PyJWTError:
                resp.status = 401
                resp.text = json.dumps({"error": "Token inválido o expirado"})
                return

            raw_body = await req.bounded_stream.read()
            data = json.loads(raw_body.decode('utf-8'))
            producto_validado = ProductoSchema(**data)

            conn = await asyncpg.connect(DATABASE_URL)
            await conn.execute(
                "INSERT INTO productos (nombre, precio, en_stock) VALUES ($1, $2, $3)",
                producto_validado.nombre, producto_validado.precio, producto_validado.en_stock
            )
            await conn.close()

            resp.status = 201
            resp.text = json.dumps({
                "mensaje": "Producto guardado en PostgreSQL (Docker)",
                "producto": producto_validado.model_dump()
            })

        except ValidationError as e:
            resp.status = 400
            resp.text = json.dumps({"error": "Validación fallida", "detalles": e.errors()})
        except Exception as e:
            resp.status = 500
            resp.text = json.dumps({"error": "Error interno del servidor", "detalle": str(e)})

    async def on_get(self, req, resp):
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            filas = await conn.fetch("SELECT id, nombre, precio, en_stock FROM productos")
            await conn.close()
            
            lista_productos = []
            for fila in filas:
                lista_productos.append({
                    "id": fila["id"],
                    "nombre": fila["nombre"],
                    "precio": fila["precio"],
                    "en_stock": bool(fila["en_stock"])
                })

            resp.status = 200
            resp.text = json.dumps({
                "total": len(lista_productos),
                "productos": lista_productos
            })
        except Exception as e:
            # Si la tabla aún no ha sido creada en la BD, devolvemos una lista vacía en lugar de un error 500
            resp.status = 200
            resp.text = json.dumps({
                "total": 0,
                "productos": [],
                "aviso": "La tabla de productos aún está vacía o pendiente de inicializar."
            })
# 3. Recurso de prueba externa
class ReporteVentasResource:
    async def on_get(self, req, resp):
        url = "https://fakestoreapi.com/products"
        async with httpx.AsyncClient() as client:
            resultado = await client.get(url)
            productos_externos = resultado.json()

        resp.status = 200
        resp.text = json.dumps({
            "estado": "éxito",
            "origen": "Fake Store API",
            "total_registros": len(productos_externos),
            "datos": productos_externos
        })

# 4. Generador del JSON de OpenAPI
class OpenApiJsonResource:
    async def on_get(self, req, resp):
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": "API Asíncrona con Falcon y PostgreSQL",
                "version": "1.0.0",
                "description": "Documentación interactiva de la API de inventario de Daniel."
            },
            "paths": {
                "/login": {
                    "post": {
                        "summary": "Autenticación de usuario",
                        "description": "Devuelve un token JWT Bearer si las credenciales son correctas."
                    }
                },
                "/productos": {
                    "get": {
                        "summary": "Listar inventario",
                        "description": "Obtiene la lista completa de productos registrados en PostgreSQL."
                    },
                    "post": {
                        "summary": "Crear un producto",
                        "description": "Inserta un nuevo producto (Requiere token JWT en los headers)."
                    }
                },
                "/reporte-ventas": {
                    "get": {
                        "summary": "Reporte externo",
                        "description": "Consulta productos de la API externa de manera asíncrona."
                    }
                }
            }
        }
        resp.status = 200
        resp.text = json.dumps(schema)

# 5. Interfaz Visual Swagger UI
html_swagger = """
<!DOCTYPE html>
<html>
<head>
    <title>API Documentación - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script>
        window.onload = () => {
            window.ui = SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
            });
        };
    </script>
</body>
</html>
"""
class SwaggerResource:
    async def on_get(self, req, resp):
        resp.status = 200
        resp.content_type = 'text/html'
        resp.text = html_swagger
# 6. Enrutamiento ASGI principal
app = App()

login_res = LoginResource()
productos_res = ProductosResource()
reporte_res = ReporteVentasResource()
openapi_res = OpenApiJsonResource()
swagger_res = SwaggerResource()

app.add_route('/login', login_res)
app.add_route('/productos', productos_res)
app.add_route('/reporte-ventas', reporte_res)
app.add_route('/openapi.json', openapi_res)
app.add_route('/docs', swagger_res)
app = App(middleware=[RateLimitMiddleware(limite_maximo=5, ventana_segundos=60)])
