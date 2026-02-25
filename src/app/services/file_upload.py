from typing import List
from fastapi import UploadFile
from pathlib import Path
import uuid
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ingestion_service import DocumentIngestionService
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)
UPLOAD_DIR = Path(settings.temp_file_path)

async def save_multiple_files(
    files: List[UploadFile],
    company_id: str,
    db: AsyncSession,
    uploader: str,
):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ingestion_service = DocumentIngestionService()
    results = []

    for file in files:
        document_id = str(uuid.uuid4())
        path = UPLOAD_DIR / f"{document_id}_{file.filename}"

        try:
            content = await file.read()
            path.write_bytes(content)

            document = await ingestion_service.ingest_document(
                file_path=str(path),
                filename=file.filename,
                company_id=company_id,
                db=db,
                uploader=uploader,
                delete_file=True
            )

            results.append({
                "document_id": document.id,
                "filename": document.filename,
                "status": document.status,
            })

        except Exception as e:
            logger.exception("Upload failed: %s", file.filename)
            results.append({
                "document_id": document_id,
                "filename": file.filename,
                "status": "failed",
            })

        finally:
            if path.exists():
                os.remove(path)

    return results