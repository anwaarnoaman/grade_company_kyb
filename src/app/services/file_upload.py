from typing import List
from fastapi import UploadFile
from pathlib import Path
import uuid
from app.services.ingestion_service import DocumentIngestionService
 
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)
UPLOAD_DIR = Path(settings.temp_file_path)

async def save_multiple_files(files: List[UploadFile],session_id:str):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for file in files:
        document_id = str(uuid.uuid4())
        path = UPLOAD_DIR / f"{document_id}_{file.filename}"

        try:
            content = await file.read()
            path.write_bytes(content)

 
            service = DocumentIngestionService()

            result = service.ingest_document(str(path), file.filename, session_id)
 
            results.append({
                "document_id": document_id,
                "filename": file.filename,
                "status": "Processed"
            })

        except Exception as e:
            logger.exception("Upload failed: %s", file.filename)
            results.append({
                "document_id": document_id,
                "filename": file.filename,
                "status": "failed"
            })

    return results
