# DW_GrupoTDM API

## Descripción del Proyecto
REST API privada desarrollada en Python (FastAPI) para la consulta ágil de vistas del Data Warehouse corporativo DW_GrupoTDM (SQL Server).

## Requisitos Previos
- Python 3.11+
- ODBC Driver 17 for SQL Server
- Docker y Docker Compose (Opcional para despliegue en contenedores)

## Instalación Local (Sin Docker)
1. **Clonar repositorio e ir a la carpeta:**
   ```bash
   git clone <repo_url>
   cd DW-GrupoTDM-API
   ```
2. **Crear y activar entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   .\venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```
3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configurar Entorno:**
   Copia el archivo `.env.example` a `.env` e ingresa tus credenciales:
   ```bash
   cp .env.example .env
   ```
5. **Ejecutar servidor:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Despliegue con Docker Compose
1. Configura tu archivo `.env`.
2. Construye y levanta el contenedor en segundo plano:
   ```bash
   docker-compose up -d --build
   ```
3. Verifica los logs:
   ```bash
   docker-compose logs -f
   ```

## Endpoints
| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/auth/login` | Obtiene un token JWT | No |
| GET | `/auth/me` | Retorna la información del usuario actual | Sí |
| GET | `/auth/verify` | Verifica si el token es válido | Sí |
| GET | `/views/` | Lista las vistas disponibles | Sí |
| GET | `/views/{view_name}/schema` | Obtiene el esquema/columnas de la vista | Sí |
| GET | `/views/{view_name}` | Consulta los datos con paginación/filtros | Sí |
| GET | `/views/{view_name}/filter` | Filtra dinámicamente por querystrings | Sí |
| POST | `/views/{view_name}/query` | Filtros complejos en JSON | Sí |
| GET | `/views/{view_name}/export` | Exporta datos a CSV o JSON | Sí |

## Ejemplos de Uso (curl)

**1. Obtener Token (Login):**
```bash
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d "{\"username\": \"admin\", \"password\": \"admin123\"}"
```
*(Guarda el `access_token` recibido)*

**2. Consultar Vista (Ej. cls_Dim_Tiendas):**
```bash
curl -X GET "http://localhost:8000/views/cls_Dim_Tiendas?limit=10" \
     -H "Authorization: Bearer <TU_TOKEN>"
```

**3. Filtrar Dinámicamente:**
```bash
curl -X GET "http://localhost:8000/views/cls_Dim_Tiendas/filter?MARCA=TDM&limit=5" \
     -H "Authorization: Bearer <TU_TOKEN>"
```

**4. Exportar a CSV:**
```bash
curl -X GET "http://localhost:8000/views/cls_Dim_Tiendas/export?format=csv" \
     -H "Authorization: Bearer <TU_TOKEN>" \
     -O -J
```

## Referencia de Variables de Entorno
| Variable | Propósito | Ejemplo |
|---|---|---|
| DB_SERVER | Dirección del servidor | 10.75.65.20\TDM-SQL-PRUEBAS |
| DB_DATABASE | Nombre BD | DW_GrupoTdm |
| DB_USERNAME | Usuario SQL | sa |
| DB_PASSWORD | Password SQL | *** |
| DB_DRIVER | Driver ODBC | ODBC Driver 17 for SQL Server |
| JWT_SECRET_KEY | Secreto JWT | secret_key_temporal_jwt |
| JWT_ALGORITHM | Algoritmo JWT | HS256 |
| JWT_EXPIRE_MINUTES | Tiempo validez token | 480 |
| ENABLE_EXPORT | Permitir exportación CSV | true |
