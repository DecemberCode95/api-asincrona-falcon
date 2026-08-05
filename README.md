# ⚡ API Asíncrona en Falcon & PostgreSQL

Una API RESTful asíncrona de alto rendimiento construida con Python, Falcon ASGI y PostgreSQL. El proyecto implementa arquitectura limpia, seguridad por capas, limitación de tasa de peticiones, validación estricta de datos y autenticación mediante JWT.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.12+
* **Framework Web:** Falcon (ASGI)
* **Servidor ASGI:** Uvicorn
* **Base de Datos:** PostgreSQL (ejecutado en contenedor Docker)
* **Conector BD:** `asyncpg` (operaciones asíncronas de base de datos)
* **Seguridad:** PyJWT, Middleware de cabeceras HTTP defensivas y Rate Limiting

---

## 🛡️ Características Principales

* **Rendimiento Asíncrono:** Gestión nativa de I/O no bloqueante con ASGI y `asyncpg`.
* **Seguridad por Capas:**
  * **Rate Limiting:** Protección contra fuerza bruta (máximo 5 peticiones/minuto en `/login`).
  * **Security Headers:** Cabeceras HTTP defensivas (CSP, HSTS, X-Content-Type-Options).
  * **Autenticación JWT:** Control de acceso a rutas protegidas mediante tokens firmados.
* **Validación Estricta de Datos:** Módulo desacoplado (`validators.py`) para filtrado de datos de entrada antes del procesamiento.
* **Documentación OpenAPI:** Esquema nativo documentado para consumo e integración estándar.

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos
* Python 3.12 o superior
* Docker / Docker Compose

### 2. Clonar el Repositorio
```bash
git clone [https://github.com/TU_USUARIO/api-asincrona-falcon.git](https://github.com/TU_USUARIO/api-asincrona-falcon.git)
cd api-asincrona-falcon