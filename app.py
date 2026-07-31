# 1. Nativas
import time
import logging
# 2. Terceros
import falcon.asgi
import httpx
# 3. Locales
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

# --- LÓGICA DE NEGOCIO ---
class ReporteVentasResource:
    async def on_get(self, req, resp):
        # Aquí simularíamos la llamada asíncrona real con httpx usando 'settings'
        resp.media = {"estado": "éxito", "mensaje": "API Operativa bajo el control de Code"}
        resp.status = falcon.HTTP_200

# --- ENSAMBLAJE ---
app = falcon.asgi.App(middleware=[TelemetriaMiddleware()])
app.add_route('/reporte-ventas', ReporteVentasResource())