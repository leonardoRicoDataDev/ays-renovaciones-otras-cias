# syntax=docker/dockerfile:1

# ============================================================
# IMAGEN BASE
# ============================================================
# Python 3.13 sobre Debian Slim.
# Reduce el tamaño de la imagen frente a una instalación
# completa de Python.
FROM python:3.13-slim

# ============================================================
# VARIABLES DE ENTORNO DE PYTHON
# ============================================================
# PYTHONDONTWRITEBYTECODE:
# Evita generar archivos .pyc y carpetas __pycache__.
#
# PYTHONUNBUFFERED:
# Permite que los logs aparezcan inmediatamente en Docker
# y en la consola de Dokploy.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ============================================================
# DIRECTORIO DE TRABAJO
# ============================================================
WORKDIR /app

# ============================================================
# INSTALACIÓN DE DEPENDENCIAS
# ============================================================
# Copiamos primero requirements.txt para aprovechar
# la caché de Docker cuando el código cambia, pero las
# dependencias permanecen iguales.
COPY requirements.txt .

# Instalamos las dependencias sin almacenar caché de pip.
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# CÓDIGO DE LA APLICACIÓN
# ============================================================
# Copiamos el código fuente al contenedor.
#
# .dockerignore excluye archivos sensibles y temporales,
# como .env, .git, venv y temp.
COPY . .

# ============================================================
# USUARIO SIN PRIVILEGIOS
# ============================================================
# Creamos un usuario específico para ejecutar FastAPI.
# Esto evita ejecutar la aplicación como root.
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

# ============================================================
# PUERTO DE LA APLICACIÓN
# ============================================================
# FastAPI escuchará en el puerto 8000.
EXPOSE 8000

# ============================================================
# EJECUCIÓN DE FASTAPI
# ============================================================
# Uvicorn inicia la aplicación definida en main.py.
#
# 0.0.0.0 permite recibir conexiones desde fuera
# del contenedor.
#
# No utilizamos --reload porque estamos en producción.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]