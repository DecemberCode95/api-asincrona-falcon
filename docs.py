def obtener_esquema_openapi(app):
    """Esquema OpenAPI autogestionado y limpio para Falcon."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "API Asíncrona de Inventario y Ventas - Falcon",
            "version": "2.0.0",
            "description": "Documentación controlada nativamente para asegurar estabilidad total."
        },
        "paths": {
            "/login": {
                "post": {
                    "summary": "Autenticación de usuario",
                    "description": "Genera un token JWT válido enviando credenciales.",
                    "responses": {
                        "200": {"description": "Token generado con éxito"},
                        "401": {"description": "Credenciales inválidas"}
                    }
                }
            },
            "/productos": {
                "get": {
                    "summary": "Listar productos",
                    "description": "Devuelve el inventario registrado en la base de datos.",
                    "responses": {
                        "200": {"description": "Lista obtenida correctamente"}
                    }
                },
                "post": {
                    "summary": "Crear producto",
                    "description": "Registra un nuevo producto en el sistema.",
                    "responses": {
                        "201": {"description": "Producto creado con éxito"}
                    }
                }
            },
            "/reporte-ventas": {
                "get": {
                    "summary": "Reporte de ventas",
                    "description": "Muestra las métricas y transacciones registradas.",
                    "responses": {
                        "200": {"description": "Reporte generado correctamente"}
                    }
                }
            }
        }
    }