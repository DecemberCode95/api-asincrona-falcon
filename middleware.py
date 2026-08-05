import time
import falcon

class RateLimitMiddleware:
    def __init__(self, limite_maximo=5, ventana_segundos=60):
        self.limite_maximo = limite_maximo
        self.ventana_segundos = ventana_segundos
        self.registros = {}

    async def process_resource(self, req, resp, resource, params):
        if req.path not in ['/login']:
            return

        cliente_ip = req.remote_addr or "127.0.0.1"
        tiempo_actual = time.time()

        if cliente_ip in self.registros:
            self.registros[cliente_ip] = [
                t for t in self.registros[cliente_ip] 
                if tiempo_actual - t < self.ventana_segundos
            ]
        else:
            self.registros[cliente_ip] = []

        if len(self.registros[cliente_ip]) >= self.limite_maximo:
            resp.status = falcon.HTTP_429
            resp.media = {
                "error": "Demasiadas solicitudes. Has superado el límite de seguridad.",
                "reintento_en_segundos": self.ventana_segundos
            }
            raise falcon.HTTPTooManyRequests(
                title="Rate Limit Exceeded",
                description="Bloqueo temporal por exceso de peticiones."
            )

        self.registros[cliente_ip].append(tiempo_actual)


# 👇 AQUÍ AGREGAS LA NUEVA CLASE ABAJO SIN BORRAR NADA DE LO ANTERIOR:

class SecurityHeadersMiddleware:
    async def process_response(self, req, resp, resource, req_succeeded):
        resp.set_header('X-Content-Type-Options', 'nosniff')
        resp.set_header('X-Frame-Options', 'DENY')
        resp.set_header('X-XSS-Protection', '1; mode=block')
        resp.set_header('Content-Security-Policy', "default-src 'self';")
