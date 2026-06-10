import logging
import re
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.middleware.rate_limit import limiter
from app.auth.dependencies import require_active_user
from app.schemas.views import ViewInfo, ColumnInfo, PaginatedResponse, QueryBody
from app.services import view_service
from app.config import settings

router = APIRouter(
    dependencies=[Depends(require_active_user)],
    tags=["Views"]
)

logger = logging.getLogger(__name__)

# Validador estricto de nombre de vista para prevención adicional de inyecciones
VIEW_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")

def validate_view_name(view_name: str) -> str:
    if len(view_name) > 100 or not VIEW_NAME_REGEX.match(view_name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nombre de vista inválido. Solo se permiten letras, números y guiones bajos (max 100 caracteres)."
        )
    return view_name

def calculate_pagination(total: int, limit: int, offset: int):
    page = (offset // limit) + 1 if limit > 0 else 1
    pages = (total + limit - 1) // limit if limit > 0 else 1
    return page, pages

@router.get(
    "/",
    response_model=List[ViewInfo],
    summary="Lista vistas disponibles",
    description="Obtiene todas las vistas disponibles en la base de datos DW_GrupoTDM (esquema dbo).",
    responses={
        200: {"description": "Lista de vistas exitosa"},
        401: {"description": "No autorizado"},
        500: {"description": "Error interno del servidor"}
    }
)
@limiter.limit("100/minute")
async def list_views(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    views = view_service.get_available_views(db)
    logger.info(f"AUDIT: Usuario '{current_user['username']}' consultó la lista de vistas disponibles.")
    return [ViewInfo(name=v, description=None) for v in views]

@router.get(
    "/{view_name}/schema",
    response_model=List[ColumnInfo],
    summary="Obtiene esquema de una vista",
    description="Retorna las columnas, tipos de datos y si aceptan nulos para la vista especificada.",
    responses={
        200: {"description": "Esquema retornado exitosamente"},
        401: {"description": "No autorizado"},
        404: {"description": "Vista no encontrada"},
        422: {"description": "Nombre de vista inválido"},
        500: {"description": "Error interno del servidor"}
    }
)
@limiter.limit("100/minute")
async def get_view_schema(
    request: Request,
    view_name: str = Path(..., description="Nombre de la vista"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    view_name = validate_view_name(view_name)
    try:
        columns = view_service.get_view_columns(db, view_name)
        logger.info(f"AUDIT: Usuario '{current_user['username']}' consultó el esquema de la vista '{view_name}'.")
        return [ColumnInfo(**col) for col in columns]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/{view_name}",
    response_model=PaginatedResponse,
    summary="Consulta genérica a una vista",
    description="Consulta todos los registros de una vista con paginación y ordenamiento opcional.",
    responses={
        200: {"description": "Consulta exitosa"},
        401: {"description": "No autorizado"},
        404: {"description": "Vista no encontrada"},
        422: {"description": "Parámetros inválidos"},
        500: {"description": "Error interno del servidor"}
    }
)
@limiter.limit("100/minute")
async def get_view_data(
    request: Request,
    view_name: str = Path(..., description="Nombre de la vista"),
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    order_by: Optional[str] = Query(None, description="Columna para ordenar"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    view_name = validate_view_name(view_name)
    try:
        result = view_service.query_view(db, view_name, filters=None, limit=limit, offset=offset, order_by=order_by)
        page, pages = calculate_pagination(result["total"], limit, offset)
        
        logger.info(f"AUDIT: Usuario '{current_user['username']}' consultó la vista '{result['view']}'. Retornó {len(result['data'])} registros.")
        
        return PaginatedResponse(
            data=result["data"],
            total=result["total"],
            limit=result["limit"],
            offset=result["offset"],
            view=result["view"],
            page=page,
            pages=pages
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/{view_name}/filter",
    response_model=PaginatedResponse,
    summary="Filtra vista por query params",
    description="Filtra dinámicamente usando parámetros en la URL (ej: ?id_bodega=001). Valida que las columnas existan.",
    responses={
        200: {"description": "Filtro exitoso"},
        401: {"description": "No autorizado"},
        404: {"description": "Vista no encontrada"},
        422: {"description": "Parámetros o columnas inválidas"},
        500: {"description": "Error interno del servidor"}
    }
)
@limiter.limit("100/minute")
async def filter_view_data(
    request: Request,
    view_name: str = Path(..., description="Nombre de la vista"),
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    order_by: Optional[str] = Query(None, description="Columna para ordenar"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    view_name = validate_view_name(view_name)
    
    reserved_params = {"limit", "offset", "order_by"}
    filters = {k: v for k, v in request.query_params.items() if k not in reserved_params}
    
    try:
        columns = view_service.get_view_columns(db, view_name)
        valid_columns = {col["column_name"].lower() for col in columns}
        
        for k in filters.keys():
            if k.lower() not in valid_columns:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                    detail=f"La columna '{k}' no existe en la vista '{view_name}'."
                )
                
        result = view_service.query_view(db, view_name, filters=filters, limit=limit, offset=offset, order_by=order_by)
        page, pages = calculate_pagination(result["total"], limit, offset)
        
        logger.info(f"AUDIT: Usuario '{current_user['username']}' filtró la vista '{result['view']}' con {filters}. Retornó {len(result['data'])} registros.")
        
        return PaginatedResponse(
            data=result["data"],
            total=result["total"],
            limit=result["limit"],
            offset=result["offset"],
            view=result["view"],
            page=page,
            pages=pages
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post(
    "/{view_name}/query",
    response_model=PaginatedResponse,
    summary="Consulta vista con un body JSON",
    description="Permite enviar un objeto JSON complejo con filtros y paginación en el body.",
    responses={
        200: {"description": "Consulta exitosa"},
        401: {"description": "No autorizado"},
        404: {"description": "Vista no encontrada"},
        422: {"description": "Estructura JSON o columnas inválidas"},
        500: {"description": "Error interno del servidor"}
    }
)
@limiter.limit("100/minute")
async def post_query_view(
    request: Request,
    body: QueryBody,
    view_name: str = Path(..., description="Nombre de la vista"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    view_name = validate_view_name(view_name)
    try:
        if body.filters:
            columns = view_service.get_view_columns(db, view_name)
            valid_columns = {col["column_name"].lower() for col in columns}
            for k in body.filters.keys():
                if k.lower() not in valid_columns:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                        detail=f"La columna '{k}' no existe en la vista '{view_name}'."
                    )
                    
        result = view_service.query_view(
            db, 
            view_name, 
            filters=body.filters, 
            limit=body.limit, 
            offset=body.offset, 
            order_by=body.order_by
        )
        page, pages = calculate_pagination(result["total"], body.limit, body.offset)
        
        logger.info(f"AUDIT: Usuario '{current_user['username']}' ejecutó POST-query en vista '{result['view']}'. Retornó {len(result['data'])} registros.")
        
        return PaginatedResponse(
            data=result["data"],
            total=result["total"],
            limit=result["limit"],
            offset=result["offset"],
            view=result["view"],
            page=page,
            pages=pages
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/{view_name}/export",
    summary="Exportar datos de una vista",
    description="Exporta datos de una vista en formato JSON o CSV (requiere ENABLE_EXPORT=true en config). Límite de 10,000 registros.",
    responses={
        200: {"description": "Archivo CSV o JSON retornado"},
        401: {"description": "No autorizado"},
        403: {"description": "Exportación deshabilitada en el servidor"},
        404: {"description": "Vista no encontrada"},
        422: {"description": "Parámetros inválidos"},
        500: {"description": "Error interno del servidor"}
    }
)
@limiter.limit("100/minute")
async def export_view_data(
    request: Request,
    view_name: str = Path(..., description="Nombre de la vista"),
    format: str = Query("json", pattern="^(json|csv)$", description="Formato de exportación ('json' o 'csv')"),
    order_by: Optional[str] = Query(None, description="Columna por la cual ordenar los datos exportados"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_active_user)
):
    if not settings.enable_export:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La exportación está deshabilitada en la configuración del servidor.")
        
    view_name = validate_view_name(view_name)
    export_limit = 10000
    
    try:
        result = view_service.query_view(db, view_name, limit=export_limit, order_by=order_by)
        data = result["data"]
        
        logger.info(f"AUDIT: Usuario '{current_user['username']}' exportó {len(data)} registros de la vista '{result['view']}' en formato {format}.")
        
        if format == "json":
            page, pages = calculate_pagination(result["total"], export_limit, 0)
            return PaginatedResponse(
                data=data,
                total=result["total"],
                limit=export_limit,
                offset=0,
                view=result["view"],
                page=page,
                pages=pages
            )
        elif format == "csv":
            if not data:
                return StreamingResponse(io.StringIO(""), media_type="text/csv")
                
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
            response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
            response.headers["Content-Disposition"] = f"attachment; filename={result['view']}_export.csv"
            return response
            
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
