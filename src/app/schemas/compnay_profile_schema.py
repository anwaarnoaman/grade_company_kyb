from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

class CompanyProfileCreate(BaseModel):
    name: str
    status: Optional[str] = "active"

class CompanyProfileRead(CompanyProfileCreate):
    id: int
    company_id: uuid.UUID
    kyb_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


 