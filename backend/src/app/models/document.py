from datetime import date

from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import UUID, Column, Date, Float, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

 
class UploadedDocument(BaseModel):
    document_id: str
    filename: str
    status: str
class GetDocument(BaseModel):
    id: str         
    filename:str  
    status: str       
    blob_path: str    
    class_type: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    language: Optional[str] = None
    confidence: Optional[float] = None
    class Config:
        from_attributes = True   
class MultiUploadResponse(BaseModel):
    total: int
    uploaded: List[UploadedDocument]

class DocumentUploadInput(BaseModel):
    session_id: str

class Document(Base):
    __tablename__ = "documents" 

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    uploader = Column(String, nullable=False)
    blob_path = Column(String, nullable=False)
    status = Column(String, default="uploaded")
    upload_time = Column(DateTime(timezone=True), server_default=func.now())    
    class_type = Column(String, nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    language = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    # link to company
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.company_id"), nullable=False)


 
