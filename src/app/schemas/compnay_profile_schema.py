from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class CompanyProfileCreate(BaseModel):
    name: str
    status: Optional[str] = "active"

class CompanyProfileRead(CompanyProfileCreate):
    id: int
    company_id: uuid.UUID

    class Config:
        from_attributes = True


 