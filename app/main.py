from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, views
from app.database import test_connection

app = FastAPI(
    title="DW GrupoTDM API",
    version="1.0.0",
    description="API privada para consulta de vistas del Data Warehouse GrupoTDM"
)

# Configuración de CORS
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

# TODO: Agregar middlewares futuros aquí

app.include_router(auth.router, prefix="/auth")
app.include_router(views.router, prefix="/views")

@app.on_event("startup")
async def startup_event():
    test_connection()

@app.get("/", tags=["Health"])
async def root():
    return {
        "api": "DW GrupoTDM API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
