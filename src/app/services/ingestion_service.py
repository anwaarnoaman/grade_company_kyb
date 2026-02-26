from abc import ABC, abstractmethod
from typing import Optional, Dict
import os
import uuid
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
        self.document_classification_pipeline = DocumentClassificationPipeline()
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
    """Processor for PDF files with concise audit logs."""

    async def process(
        self,
        file_path: str,
        filename: str,
        company_id: str,
        db: AsyncSession,
        uploader: str,
        delete_file: bool = True
    ):
        document_id = str(uuid.uuid4())

        try:
            # Upload file to blob storage
            blob_service = AzureBlobService()
            upload_result = blob_service.upload_file(
                file_path=file_path,
                filename=filename,
                content_type="application/pdf"
            )
            blob_path = upload_result["blob_name"]

            # Classify and extract document info
            result = self.document_classification_pipeline.process_document(file_path)
            classType = result["classType"]
            issueDate = result["issueDate"]
            expiryDate = result["expiryDate"]
            confidence = result["confidence"]
            language = result["language"]

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
                        "class_type": classType,
                        "issue_date": str_to_date(issueDate),
                        "expiry_date": str_to_date(expiryDate),
                        "confidence": confidence,
                        "language": language
                    }
                ]
            )

            if delete_file:
                self._cleanup_uploaded_file(file_path)

            document = document_list[0] if document_list else None

            # Concise audit log
            self.logger.info(
                "DOCUMENT_INGESTION_SUCCESS",
                extra={
                    "audit": True,
                    "event_type": "DOCUMENT_INGESTION_SUCCESS",
                    "doc_name": filename,
                    "document_id": document.id if document else document_id,
                    "company_id": company_id,
                    "uploader": uploader,
                    "class_type": classType,
                    "confidence": confidence,
                    "language": language,
                    "issue_date": issueDate,
                    "expiry_date": expiryDate
                }
            )

            return document

        except Exception as e:
            self.logger.error(
                "DOCUMENT_INGESTION_FAILED",
                extra={
                    "audit": True,
                    "event_type": "DOCUMENT_INGESTION_FAILED",
                    "doc_name": filename,
                    "document_id": document_id,
                    "company_id": company_id,
                    "uploader": uploader,
                    "error": str(e),
                }
            )
            raise

class OtherProcessor(BaseProcessor):
    """Processor for unrecognized file types."""

    async def process(
        self,
        file_path: str,
        filename: str,
        company_id: str,
        db: AsyncSession,
        uploader: str,
        delete_file: bool = True
    ) -> Optional[str]:
        document_id = str(uuid.uuid4())
        self.logger.warning(
            "UNSUPPORTED_DOCUMENT",
            extra={
                "audit": True,
                "event_type": "UNSUPPORTED_DOCUMENT",
                "doc_name": filename,
                "document_id": document_id,
                "company_id": company_id,
            }
        )

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
        file_type = detect_file_type(file_path)
        processor_class = self._processor_map.get(file_type, OtherProcessor)
        processor = processor_class(company_id)

        # Only call processor.process(), no extra start logs here
        return await processor.process(
            file_path=file_path,
            filename=filename,
            company_id=company_id,
            db=db,
            uploader=uploader,
            delete_file=delete_file,
        )