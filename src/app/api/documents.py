from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List

from app.services.file_upload import save_multiple_files
from app.models.document import MultiUploadResponse
from app.core.logging import get_logger
from app.core.dependencies import get_current_user  # JWT dependency

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=MultiUploadResponse)
async def upload_documents(
    session_id: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user = Depends(get_current_user)  # JWT authentication
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Audit logging with user info
    logger.info(
        "User %s (ID: %s) is uploading %d files for session %s",
        current_user.username,
        current_user.user_id,
        len(files),
        session_id
    )

    try:
        results = await save_multiple_files(files, session_id)
        return MultiUploadResponse(
            total=len(files),
            uploaded=results,
        )
    except Exception:
        logger.exception(
            "File upload failed for user %s (ID: %s)",
            current_user.username,
            current_user.user_id
        )
        raise HTTPException(status_code=500, detail="Upload failed")