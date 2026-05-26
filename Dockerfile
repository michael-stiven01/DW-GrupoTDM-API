FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema para pyodbc + SQL Server
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root "appuser"
RUN useradd -m appuser

# Directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero (aprovecha layer caching)
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Asignar permisos al usuario no-root
RUN chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK CMD curl -f http://localhost:8000/ || exit 1

# Comando por defecto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
