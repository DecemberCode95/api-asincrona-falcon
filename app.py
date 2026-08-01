import time
import logging
import falcon.asgi
import httpx
from pydantic import BaseModel, ValidationError
from config import settings

# --- CONFIGURACIÓN BASE ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CodeAPI")

# --- MIDDLEWARE (Observador) ---
class TelemetriaMiddleware:
    async def process_request(self, req, resp):
        req.context.inicio_tiempo = time.time()
        logger.info(f"📥 Entrando: {req.method} {req.path}")

    async def process_response(self, req, resp, resource, req_succeeded):
        if hasattr(req.context, 'inicio_tiempo'):
            tiempo = (time.time() - req.context.inicio_tiempo) * 1000
            logger.info(f"📤 Saliendo: {req.method} {req.path} | {tiempo:.2f}ms")

# --- ESQUEMAS DE VALIDACIÓN (El Guardaespaldas Pydantic) ---
class ProductoNuevo(BaseModel):
    nombre: str          # Obligatorio que sea texto
    precio: float        # Obligatorio que sea un número (con o sin decimales)
    en_stock: bool       # Obligatorio que sea Verdadero o Falso

# --- LÓGICA DE NEGOCIO ---

# Ruta 1: Nosotros pedimos datos (GET)
class ReporteVentasResource:
    async def on_get(self, req, resp):
        url_ventas = "https://fakestoreapi.com/products?limit=3"
        try:
            async with httpx.AsyncClient() as client:
                respuesta_externa = await client.get(url_ventas, timeout=5.0)
                respuesta_externa.raise_for_status()
                datos_ventas = respuesta_externa.json()

            resp.media = {
                "estado": "éxito",
                "origen": "Fake Store API",
                "total_registros": len(datos_ventas),
                "datos": datos_ventas
            }
            resp.status = falcon.HTTP_200

        except httpx.HTTPError as error_red:
            logger.error(f"💥 Error de red: {error_red}")
            resp.media = {"estado": "fallo", "error": "No se pudo conectar con el proveedor."}
            resp.status = falcon.HTTP_502

# Ruta 2: El usuario nos envía datos (POST)
class CrearProductoResource:
    async def on_post(self, req, resp):
        try:
            # 1. Leemos los datos crudos que nos envía el cliente
            datos_crudos = await req.get_media()
            
            # 2. Pasamos los datos por el guardaespaldas (Pydantic)
            producto_validado = ProductoNuevo(**datos_crudos)
            
            # 3. Si llega a esta línea, los datos son perfectos
            resp.media = {
                "estado": "éxito",
                "mensaje": f"Producto '{producto_validado.nombre}' aceptado en el sistema."
            }
            resp.status = falcon.HTTP_201 # 201 significa "Creado exitosamente"
            
        except ValidationError as e:
            # Si el cliente envía datos malos (ej: un precio en letras), lo bloqueamos
            logger.warning("🛡️ Pydantic bloqueó una petición inválida.")
            resp.media = {"estado": "rechazado", "errores": e.errors()}
            resp.status = falcon.HTTP_400 # 400 significa "Mala petición del cliente"

# --- ENSAMBLAJE ---
app = falcon.asgi.App(middleware=[TelemetriaMiddleware()])
app.add_route('/reporte-ventas', ReporteVentasResource())
app.add_route('/productos', CrearProductoResource())