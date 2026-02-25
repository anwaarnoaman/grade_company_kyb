from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db_dependencies import get_db
from app.core.auth_dependencies import get_current_user
 
from app.core.logging import get_logger
from app.schemas.compnay_profile_schema import CompanyProfileCreate, CompanyProfileRead
from app.services.db.company_profile_service import CompanyProfileService
 

logger = get_logger(__name__)

router = APIRouter(prefix="/companies", tags=["Companies"])
service = CompanyProfileService()

@router.post("/", response_model=CompanyProfileRead)
async def create_company_profile(
    company_data: CompanyProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user), 
):
    """
    Create a new company profile.
    """
    try:
        logger.info(
            "User %s (ID: %s) creating company profile: %s",
            current_user.username,
            current_user.user_id,
            company_data.name,
        )

        new_company = await service.create_company(db=db, data=company_data.dict())

        return new_company

    except Exception:
        logger.exception(
            "Failed to create company profile: %s by user %s (ID: %s)",
            company_data.name,
            current_user.username,
            current_user.user_id,
        )
        raise HTTPException(status_code=500, detail="Failed to create company profile")