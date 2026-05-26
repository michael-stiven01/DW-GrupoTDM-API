from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ViewInfo(BaseModel):
    name: str
    description: Optional[str] = None

class ColumnInfo(BaseModel):
    column_name: str
    data_type: str
    is_nullable: str

class PaginatedResponse(BaseModel):
    data: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int
    view: str
    page: int
    pages: int

class QueryBody(BaseModel):
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=100, ge=1, le=5000)
    offset: int = Field(default=0, ge=0)
    order_by: Optional[str] = None
