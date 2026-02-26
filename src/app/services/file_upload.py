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

    # -------------------------------
    # AUDIT LOG: User upload summary
    # -------------------------------
    uploaded_files = [r for r in results if r["status"] != "failed"]
    failed_files = [r for r in results if r["status"] == "failed"]

    logger.info(
        f"User uploaded {len(files)} file(s) | Successful: {len(uploaded_files)} | Failed: {len(failed_files)}",
        extra={
            "audit": True,
            "event_type": "USER_UPLOAD_BATCH",
            "company_id": company_id,
            "actor": uploader,
            "uploaded_files": [f["filename"] for f in uploaded_files],
            "failed_files": [f["filename"] for f in failed_files],
            "total_files": len(files),
            "success_count": len(uploaded_files),
            "failed_count": len(failed_files),
        }
    )

    return results