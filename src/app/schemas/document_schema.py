import uuid

from pydantic import BaseModel
from datetime import datetime

class DocumentCreate(BaseModel):
    filename: str
    content_type: str
    uploader: str
    blob_path: str
    status: str = "uploaded"
    company_id: uuid.UUID  # now required

class DocumentRead(DocumentCreate):
    id: str
    upload_time: datetime

    class Config:
        from_attributes = True