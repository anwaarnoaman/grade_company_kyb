from alembic.util import status
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List
from sqlalchemy import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID as pyUUID
from app.core.db_dependencies import get_db
from app.models.document import  Document, GetDocument, MultiUploadResponse, UploadedDocument 
from app.services.db.document_service import DocumentService
from app.services.file_upload import save_multiple_files
from app.core.logging import get_logger
from app.core.auth_dependencies import get_current_user 
logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])
service = DocumentService()

@router.post("/upload", response_model=MultiUploadResponse)
async def upload_documents(
    company_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    logger.info(
        "User %s (ID: %s) uploading %d files for session %s",
        current_user.username,
        current_user.user_id,
        len(files),
        company_id,
    )

    try:
        results = await save_multiple_files(
            files=files,
            company_id=company_id,
            db=db,
            uploader=current_user.username,
        )

        return MultiUploadResponse(
            total=len(files),
            uploaded=results,
        )

    except Exception:
        logger.exception(
            "File upload failed for user %s (ID: %s)",
            current_user.username,
            current_user.user_id,
        )
        raise HTTPException(status_code=500, detail="Upload failed")
    

@router.get("/by-company/{company_id}", response_model=List[GetDocument])
async def get_documents_by_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        # fetch all documents for the company
        documents: List[Document] = await service.get_documents_by_company(db, company_id)

        # convert to Pydantic models
        return [GetDocument.from_orm(doc) for doc in documents]

    except Exception as e:
        import logging
        logging.error(f"Failed to fetch documents for company_id {company_id} by user {user.username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents")