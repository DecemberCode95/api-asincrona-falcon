import json
import httpx
import jwt
import asyncpg
import falcon
from falcon.asgi import App
from typing import Optional, Dict, Any

# Módulos locales del proyecto
from docs import obtener_esquema_openapi
from middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from database import listar_productos, DATABASE_URL
from validators import ProductoValidator
from core.logging_config import logger

# Llave secreta para firmar los tokens JWT (mínimo 32 caracteres para seguridad)
SECRET_KEY = "super-secreto-seguro-de-daniel-2024-v1"
ALGORITHM = "HS256"


# 1. Recurso de Autenticación (Login)
class LoginResource:
    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        """POST /login - Autentica usuarios y retorna token JWT"""
        try:
            raw_body: bytes = await req.bounded_stream.read()  # type: ignore
            data: Dict[str, Any] = json.loads(raw_body.decode('utf-8'))
            usuario: Optional[str] = data.get("username") or data.get("usuario")
            
            logger.info(f"Intento de login para usuario: {usuario}")

            # Validación flexible de llaves
            password: Optional[str] = data.get("password") or data.get("contrasena")

            if usuario == "admin" and password == "password123":
                payload: Dict[str, str] = {"sub": usuario, "rol": "admin"}
                token: str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
                
                logger.info(f"✅ Login exitoso para usuario: {usuario}")

                resp.status = falcon.HTTP_200
                resp.text = json.dumps({
                    "mensaje": "Autenticación exitosa",
                    "access_token": token,
                    "token": token,
                    "tipo": "Bearer"
                })
            else:
                logger.warning(f"❌ Login fallido - Credenciales inválidas para: {usuario}")
                resp.status = falcon.HTTP_401
                resp.text = json.dumps({"error": "Credenciales inválidas"})

        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido en login: {str(e)}")
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({"error": "Petición JSON inválida"})
        except Exception as e:
            logger.error(f"Error inesperado en login: {str(e)}", exc_info=True)
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({"error": "Petición JSON inválida", "detalle": str(e)})


# 2. Recurso de Productos
class ProductosResource:
    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        """POST /productos - Crea nuevo producto (requiere autenticación)"""
        try:
            # Validación de Token JWT
            auth_header: Optional[str] = req.get_header("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning("Intento de POST /productos sin token JWT")
                resp.status = falcon.HTTP_401
                resp.text = json.dumps({"error": "Acceso denegado. Falta el Token JWT"})
                return

            token: str = auth_header.split(" ")[1]
            try:
                jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                logger.debug("Token JWT validado correctamente")
            except jwt.PyJWTError as jwt_err:
                logger.warning(f"Token JWT inválido: {str(jwt_err)}")
                resp.status = falcon.HTTP_401
                resp.text = json.dumps({"error": "Token inválido o expirado"})
                return

            # Lectura del cuerpo de la petición
            raw_body: bytes = await req.bounded_stream.read()  # type: ignore
            data: Dict[str, Any] = json.loads(raw_body.decode('utf-8'))
            logger.debug(f"Datos recibidos para nuevo producto: {data.get('nombre', 'sin nombre')}")

            # 🛡️ Validación de datos con validators.py
            errores: Dict[str, str] = ProductoValidator.validar_creacion(data)
            if errores:
                logger.warning(f"Validación fallida en POST /productos: {errores}")
                resp.status = falcon.HTTP_400
                resp.text = json.dumps({
                    "error": "Falló la validación de los datos de entrada.",
                    "detalles": errores
                })
                return

            # Conexión e inserción en PostgreSQL
            try:
                conn = await asyncpg.connect(DATABASE_URL)
                precio_float: float = float(data.get("precio", 0))
                await conn.execute(
                    "INSERT INTO productos (nombre, precio, en_stock) VALUES ($1, $2, $3)",
                    data.get("nombre"),
                    precio_float,
                    bool(data.get("stock", True))
                )
                await conn.close()
                logger.info(f"✅ Producto creado: {data.get('nombre')} - ${data.get('precio')}")

            except ValueError as ve:
                logger.error(f"Error de conversión de tipo: {str(ve)}")
                resp.status = falcon.HTTP_400
                resp.text = json.dumps({"error": "Tipo de dato inválido", "detalle": str(ve)})
                return
            except Exception as db_error:
                logger.error(f"Error en BD al crear producto: {str(db_error)}", exc_info=True)
                resp.status = falcon.HTTP_500
                resp.text = json.dumps({"error": "Error interno del servidor", "detalle": str(db_error)})
                return

            # Respuesta exitosa
            resp.status = falcon.HTTP_201
            resp.text = json.dumps({
                "mensaje": "Producto guardado en PostgreSQL (Docker)",
                "producto": data
            })

        except Exception as e:
            logger.error(f"Error inesperado en POST /productos: {str(e)}", exc_info=True)
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": "Error interno del servidor", "detalle": str(e)})

    async def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        """GET /productos - Lista productos con paginación"""
        try:
            logger.debug("Iniciando GET /productos")
            
            # Parámetros de paginación
            page: int = int(req.get_param("page", default=1))
            limit: int = int(req.get_param("limit", default=10))
            
            # Validación
            if page < 1:
                page = 1
            if limit < 1:
                limit = 10
            if limit > 100:  # Máximo 100 por razones de rendimiento
                limit = 100
            
            offset: int = (page - 1) * limit
            
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

            # Obtener total de productos
            total: int = await conn.fetchval("SELECT COUNT(*) FROM productos") or 0
            
            # Consulta de registros paginados
            filas = await conn.fetch(
                "SELECT id, nombre, precio, en_stock FROM productos ORDER BY id LIMIT $1 OFFSET $2",
                limit,
                offset
            )
            await conn.close()

            lista_productos: list = []
            for fila in filas:
                lista_productos.append({
                    "id": fila["id"],
                    "nombre": fila["nombre"],
                    "precio": float(fila["precio"]),
                    "en_stock": bool(fila["en_stock"])
                })

            # Calcular número total de páginas
            total_pages: int = (total + limit - 1) // limit
            
            logger.info(f"✅ {len(lista_productos)} productos listados (página {page}/{total_pages})")
            resp.status = falcon.HTTP_200
            resp.text = json.dumps({
                "data": lista_productos,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": total_pages
                }
            })
        except ValueError as ve:
            logger.error(f"Error de validación en paginación: {str(ve)}")
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({"error": "Parámetros de paginación inválidos"})
        except Exception as e:
            logger.error(f"Error al consultar productos: {str(e)}", exc_info=True)
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

logger.info("✅ API Falcon iniciada correctamente")