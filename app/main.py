import time
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.routers import auth, views
from app.database import test_connection
from app.config import settings
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DW GrupoTDM API",
    version="1.0.0",
    description="API privada para consulta de vistas del Data Warehouse GrupoTDM"
)

# SlowAPI para Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
origins = [
    "http://localhost",
    "http://127.0.0.1",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TrustedHostMiddleware
allowed_hosts = [h.strip() for h in settings.allowed_hosts.split(",") if h.strip()]
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# Middlewares de logging y seguridad HTTP
@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000
    
    # Logging
    logger.info(
        f"METHOD: {request.method} PATH: {request.url.path} "
        f"STATUS: {response.status_code} TIME: {process_time_ms:.2f}ms"
    )
    
    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
    return response

app.include_router(auth.router, prefix="/auth")
app.include_router(views.router, prefix="/views")

@app.get("/", tags=["Health"])
async def root():
    return {
        "api": "DW GrupoTDM API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
