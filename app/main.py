import time
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.routers import auth, views
from app.database import test_connection
from app.config import settings
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

# Configuración base
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="API privada para consulta de vistas del Data Warehouse GrupoTDM",
    # Deshabilitar OpenAPI en producción
    openapi_url=None if settings.environment == "production" else "/openapi.json"
)

# Custom OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["tags"] = [
        {"name": "Auth", "description": "Endpoints para login y gestión de tokens JWT"},
        {"name": "Views", "description": "Consulta de vistas del Data Warehouse GrupoTDM"}
    ]
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema.get("paths", {}):
        for method in openapi_schema["paths"][path]:
            # No pedir token para el login ni para la raíz
            if path not in ["/auth/login", "/"]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
                
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# SlowAPI para Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middlewares de seguridad y logging
# Se declaran en orden específico de ejecución: TrustedHost -> SecurityHeaders -> RateLimit(dependencias) -> Logging

# Hosts permitidos — soporta "*" como comodín o lista separada por comas
raw_allowed_hosts = settings.allowed_hosts.strip()
if raw_allowed_hosts == "*":
    allowed_hosts_list = ["*"]
else:
    allowed_hosts_list = [h.strip() for h in raw_allowed_hosts.split(",") if h.strip()]

# CORS: usa los mismos orígenes pero con protocolo
if "*" in allowed_hosts_list:
    cors_origins = ["*"]
else:
    cors_origins = (
        [f"http://{h}" for h in allowed_hosts_list] +
        [f"https://{h}" for h in allowed_hosts_list]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,  # credentials=True no es compatible con origin=*
    allow_methods=["*"],
    allow_headers=["*"],
)

# TrustedHostMiddleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts_list)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000
    
    logger.info(
        f"METHOD: {request.method} PATH: {request.url.path} "
        f"STATUS: {response.status_code} TIME: {process_time_ms:.2f}ms"
    )
    return response

app.include_router(auth.router, prefix="/auth")
app.include_router(views.router, prefix="/views")

@app.get("/", tags=["Health"])
async def root():
    return {
        "api": app.title,
        "version": app.version,
        "status": "healthy"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
