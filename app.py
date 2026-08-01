import json
import httpx
import aiosqlite
import jwt  # <--- Librería para generar y verificar tokens
from falcon.asgi import App
from pydantic import BaseModel, Field, ValidationError
from database import iniciar_db, DB_NAME

# Llave secreta para firmar los tokens (en producción esto va en una variable de entorno oculta)
SECRET_KEY = "super-secreto-seguro-de-daniel"
ALGORITHM = "HS256"

# 1. Esquemas de Pydantic
class ProductoSchema(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    precio: float = Field(..., gt=0)
    en_stock: bool

class LoginSchema(BaseModel):
    usuario: str
    password: str

# 2. Recurso de Autenticación (El Cadenero / Login)
class LoginResource:
    async def on_post(self, req, resp):
        try:
            raw_body = await req.bounded_stream.read()
            data = json.loads(raw_body.decode('utf-8'))
            credenciales = LoginSchema(**data)

            # Validamos un usuario quemado de prueba (Admin)
            if credenciales.usuario == "admin" and credenciales.password == "password123":
                # Creamos el Token criptográfico VIP
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

# 3. Recurso de Productos (Protegido con Candado JWT)
class ProductosResource:
    async def on_post(self, req, resp):
        try:
            # EXIGIMOS LA MANILLA (Verificación del Token en los Headers)
            auth_header = req.get_header("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                resp.status = 401
                resp.text = json.dumps({"error": "Acceso denegado. Falta el Token JWT en los headers"})
                return

            token = auth_header.split(" ")[1]
            
            # Decodificamos y validamos la firma criptográfica
            try:
                jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            except jwt.PyJWTError:
                resp.status = 401
                resp.text = json.dumps({"error": "Token inválido o expirado"})
                return

            # Si pasa el candado, procedemos a guardar en el disco duro
            raw_body = await req.bounded_stream.read()
            data = json.loads(raw_body.decode('utf-8'))
            producto_validado = ProductoSchema(**data)

            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute(
                    "INSERT INTO productos (nombre, precio, en_stock) VALUES (?, ?, ?)",
                    (producto_validado.nombre, producto_validado.precio, producto_validado.en_stock)
                )
                await db.commit()

            resp.status = 201
            resp.text = json.dumps({
                "mensaje": "Producto guardado permanentemente con autorización JWT",
                "producto": producto_validado.model_dump()
            })

        except ValidationError as e:
            resp.status = 400
            resp.text = json.dumps({"error": "Validación fallida", "detalles": e.errors()})
        except Exception as e:
            resp.status = 500
            resp.text = json.dumps({"error": "Error interno del servidor", "detalle": str(e)})

    async def on_get(self, req, resp):
        # Esta ruta sigue siendo pública para consultar el inventario libremente
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT id, nombre, precio, en_stock FROM productos") as cursor:
                filas = await cursor.fetchall()
                
                lista_productos = []
                for fila in filas:
                    lista_productos.append({
                        "id": fila[0],
                        "nombre": fila[1],
                        "precio": fila[2],
                        "en_stock": bool(fila[3])
                    })

        resp.status = 200
        resp.text = json.dumps({
            "total": len(lista_productos),
            "productos": lista_productos
        })

# 4. Recurso de prueba externa
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

# 5. Enrutamiento ASGI
app = App()

login_res = LoginResource()
productos_res = ProductosResource()
reporte_res = ReporteVentasResource()

app.add_route('/login', login_res)
app.add_route('/productos', productos_res)
app.add_route('/reporte-ventas', reporte_res)