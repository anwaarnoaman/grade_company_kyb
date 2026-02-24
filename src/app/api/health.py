from fastapi import APIRouter, Depends
from app.core.logging import get_logger
from app.core.dependencies import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check(current_user = Depends(get_current_user)):
    logger.info(f"Health check accessed by user: {current_user.username} (ID: {current_user.user_id})")
    return {"status": "ok"}