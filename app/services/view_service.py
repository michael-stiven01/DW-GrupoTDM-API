import logging
import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Caché en memoria con TTL de 5 minutos (300 segundos)
_views_cache = {
    "data": None,
    "timestamp": 0
}
CACHE_TTL_SECONDS = 300

def get_available_views(db: Session) -> List[str]:
    """Obtiene la lista de vistas disponibles en el esquema dbo"""
    global _views_cache
    current_time = time.time()
    
    if _views_cache["data"] is not None and (current_time - _views_cache["timestamp"]) < CACHE_TTL_SECONDS:
        return _views_cache["data"]

    logger.info("Consultando INFORMATION_SCHEMA.VIEWS en base de datos...")
    try:
        query = text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.VIEWS 
            WHERE TABLE_SCHEMA = 'dbo' 
            ORDER BY TABLE_NAME
        """)
        result = db.execute(query)
        views = [row[0] for row in result.fetchall()]
        
        _views_cache["data"] = views
        _views_cache["timestamp"] = current_time
        
        return views
    except Exception as e:
        logger.error(f"Error obteniendo vistas disponibles: {e}")
        raise

def view_exists(db: Session, view_name: str) -> bool:
    """Verifica si una vista existe (case-insensitive)"""
    available_views = get_available_views(db)
    return any(v.lower() == view_name.lower() for v in available_views)

def get_view_columns(db: Session, view_name: str) -> List[Dict[str, str]]:
    """Obtiene las columnas de una vista desde INFORMATION_SCHEMA.COLUMNS"""
    if not view_exists(db, view_name):
        raise ValueError(f"La vista {view_name} no existe.")
        
    try:
        query = text("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = :view_name
            ORDER BY ORDINAL_POSITION
        """)
        result = db.execute(query, {"view_name": view_name})
        columns = []
        for row in result.fetchall():
            columns.append({
                "column_name": row[0],
                "data_type": row[1],
                "is_nullable": row[2]
            })
        return columns
    except Exception as e:
        logger.error(f"Error obteniendo columnas de la vista {view_name}: {e}")
        raise

def query_view(
    db: Session,
    view_name: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 100,
    offset: int = 0,
    order_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Consulta registros de una vista con paginación y filtros opcionales.
    """
    if not view_exists(db, view_name):
        raise ValueError(f"View not found: {view_name}")

    limit = min(limit, 5000)
    
    try:
        available_views = get_available_views(db)
        real_view_name = next(v for v in available_views if v.lower() == view_name.lower())
        
        base_query = f"SELECT * FROM dbo.[{real_view_name}]"
        count_query = f"SELECT COUNT(*) FROM dbo.[{real_view_name}]"
        
        where_clauses = []
        params = {}
        
        if filters:
            for key, value in filters.items():
                safe_key = key.replace("]", "").replace("[", "")
                where_clauses.append(f"[{safe_key}] = :val_{safe_key}")
                params[f"val_{safe_key}"] = value
                
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)
            base_query += where_sql
            count_query += where_sql
            
        total_count = db.execute(text(count_query), params).scalar()
        
        if order_by:
            safe_order = order_by.replace("]", "").replace("[", "").split()[0]
            base_query += f" ORDER BY [{safe_order}]"
        else:
            cols = get_view_columns(db, real_view_name)
            first_col = cols[0]["column_name"]
            base_query += f" ORDER BY [{first_col}]"
            
        base_query += " OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params["offset"] = offset
        params["limit"] = limit
        
        result = db.execute(text(base_query), params)
        
        data = []
        for row in result.mappings().all():
            data.append(dict(row))
            
        return {
            "data": data,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "view": real_view_name
        }
        
    except Exception as e:
        logger.error(f"Error consultando la vista {view_name}: {e}")
        raise
