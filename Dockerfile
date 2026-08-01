# 1. Traemos un mini-sistema operativo Linux con Python ya instalado (versión ligera)
FROM python:3.14-slim

# 2. Creamos una carpeta de trabajo dentro de la caja fuerte
WORKDIR /app

# 3. Copiamos ÚNICAMENTE el inventario primero (Truco de ingeniería para que sea más rápido)
COPY requirements.txt .

# 4. Instalamos las herramientas leyendo el inventario
RUN pip install --no-cache-dir -r requirements.txt

# 5. Ahora sí, copiamos el resto de tu código (app.py, test_app.py, etc.)
COPY . .

# 6. Le decimos a la caja que tiene permiso de abrir la puerta 8000
EXPOSE 8000

# 7. La orden de encendido automático. 
# Usamos 0.0.0.0 en lugar de 127.0.0.1 para que el contenedor permita conexiones desde afuera.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]