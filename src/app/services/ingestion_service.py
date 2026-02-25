from abc import ABC, abstractmethod
from typing import Optional, Dict, Callable
import os
from app.core.logging import get_logger 
from app.services.azure.azure_blob_service import AzureBlobService
from app.services.db.document_service import DocumentService
from app.services.kyb_pipeline.document_classification_pipeline import DocumentClassificationPipeline
from app.utils.file import detect_file_type
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.misc import str_to_date



logger = get_logger(__name__)

class BaseProcessor(ABC):
    """Abstract base class for all document processors."""
    
    def __init__(self, session_id: str):

        self.session_id = session_id
        self.temp_folder = settings.temp_file_path
        self.db_path = os.path.join(self.temp_folder, f"{session_id}.db")
        self.document_service = DocumentService()
        self.document_classification_pipeline=DocumentClassificationPipeline()

        self.logger = logger
    
    @abstractmethod
    async def process(
        self,
        file_path: str,
        filename: str,
        session_id: str,
        db: AsyncSession,
        uploader: str,
        delete_file: bool = True
    ):
        """Process the document and return DB object."""
        pass
    
    def _ensure_temp_folder(self):
        """Create temp folder if it doesn't exist."""
        os.makedirs(self.temp_folder, exist_ok=True)
    
    def _cleanup_uploaded_file(self, file_path: str):
        """Delete the uploaded file after processing."""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                self.logger.info("Deleted uploaded file: %s", file_path)
            except Exception as e:
                self.logger.warning("Failed to delete uploaded file %s: %s", file_path, e)
    
class PDFProcessor(BaseProcessor):
    """Processor for PDF files."""
    
    async def process(
        self, 
        file_path: str, 
        filename: str, 
        company_id: str, 
        db: AsyncSession, 
        uploader: str,
        delete_file: bool = True
    ):
        self.logger.info("Processing PDF file: %s | company_id=%s", filename, company_id)

        blob_service = AzureBlobService()
        
        upload_result = blob_service.upload_file(
            file_path=file_path,
            filename=filename,
            content_type="application/pdf"
        )

        blob_path = upload_result["blob_name"]

        #Documetn classification and metadata exraction
        result = self.document_classification_pipeline.process_document(file_path) 
        classType=result["classType"]
        issueDate=result["issueDate"]
        expiryDate=result["expiryDate"]
        confidence=result["confidence"]
        language=result["language"]
        
        
        # Save metadata in DB
        document_list = await self.document_service.upload_documents(
            db,
            [
                {
                    "filename": filename,
                    "content_type": "application/pdf",
                    "uploader": uploader,
                    "blob_path": blob_path,
                    "status": "uploaded",
                    "company_id": company_id,
                    "class_type":classType,
                    "issue_date":str_to_date(issueDate),
                    "expiry_date":str_to_date(expiryDate),
                    "confidence":confidence,
                    "language":language


                }
            ]
        )

        if delete_file:
            self._cleanup_uploaded_file(file_path)

        document = document_list[0] if document_list else None  # safely get the first
        return document

class OtherProcessor(BaseProcessor):
    """Processor for unrecognized file types."""
    
    def process(self, file_path: str, filename: str,delete_file: bool = True) -> Optional[str]:
        """Process other file types."""
        self.logger.info("Processing other file: %s | session_id=%s", filename, self.session_id)
        # TODO: Implement generic processing
        self._cleanup_uploaded_file(file_path)
        return None

class DocumentIngestionService:
    """Main service class for document ingestion."""
    
    def __init__(self):
        self.logger = logger
        self._processor_map: Dict[str, type[BaseProcessor]] = {
            'pdf': PDFProcessor,
            'other': OtherProcessor,
        }
    
     
    async def ingest_document(
            self, 
            file_path: str, 
            filename: str, 
            company_id: str, 
            db: AsyncSession, 
            uploader: str,
            delete_file: bool = True
        ):
            self.logger.info("Processing %s", filename)

            file_type = detect_file_type(file_path)
            self.logger.info("Detected file type: %s", file_type)

            processor_class = self._processor_map.get(file_type, OtherProcessor)
            processor = processor_class(company_id)

            result = await processor.process(
                file_path=file_path,
                filename=filename,
                company_id=company_id,
                db=db,
                uploader=uploader,
                delete_file=delete_file,
            )

            return result