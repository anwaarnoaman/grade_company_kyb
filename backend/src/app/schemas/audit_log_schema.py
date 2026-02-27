from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class AuditLogCreate(BaseModel):
    company_id: Optional[uuid.UUID] = None
    user_name: Optional[str] = None
    action: Optional[str] = None
    table_name: Optional[str] = None
    record_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    message: Optional[str] = None  


class AuditLogRead(AuditLogCreate):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True