from typing import List

from fastapi import APIRouter, Body, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db_dependencies import get_db
from app.core.auth_dependencies import get_current_user
 
from app.core.logging import get_logger
from app.schemas.compnay_profile_schema import CompanyProfileCreate, CompanyProfileRead
from app.services.db.company_profile_service import CompanyProfileService
from app.services.kyb_generation_service import KYBGenerationService
 

logger = get_logger(__name__)

router = APIRouter(prefix="/companies", tags=["Companies"])
service = CompanyProfileService()
kyb_service = KYBGenerationService()




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
    

@router.get("/", response_model=List[CompanyProfileRead])
async def get_all_companies(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve all company profiles.
    """
    try:
        logger.info(
            "User %s (ID: %s) requested all company profiles",
            current_user.username,
            current_user.user_id,
        )

        companies = await service.get_all_companies(db=db)
        return companies

    except Exception:
        logger.exception(
            "Failed to fetch all companies for user %s (ID: %s)",
            current_user.username,
            current_user.user_id,
        )
        raise HTTPException(status_code=500, detail="Failed to fetch companies")


@router.post("/{company_id}/generate-kyb")
async def generate_company_kyb(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate KYB report for a company.
    """

    try:
        logger.info(
            "User %s (ID: %s) requested KYB generation for company_id=%s",
            current_user.username,
            current_user.user_id,
            company_id,
        )
 
        # Run KYB process
        result =await kyb_service.process(db=db,company_id=company_id)

        return {
            "status": "success",
            "company_id": company_id,
            "kyb_result": result,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed KYB generation for company_id=%s by user %s (ID: %s)",
            company_id,
            current_user.username,
            current_user.user_id,
        )
        raise HTTPException(status_code=500, detail="Failed to generate KYB")
    
@router.post("/{company_id}/save_profile")
async def save_profile( 
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Save manual edits to KYB profile.
    """
    try:
        kyb_data = payload.get("kyb_data")
        manual_edits = payload.get("manual_edits", [])
        company_id=kyb_data["company_id"],  
        if not kyb_data:
            raise HTTPException(status_code=400, detail="kyb_data missing")

        updated_data = await service.save_manual_edits(
            db=db,
            company_id=company_id,
            kyb_data=kyb_data["kyb_result"],
            manual_edits=manual_edits,
            actor=current_user.username,
        )

        return {"status": "success", "company_id": company_id, "updated_data": updated_data}

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to save profile for company_id=%s by user %s (ID: %s)",
            company_id,
            current_user.username,
            current_user.user_id,
        )
        raise HTTPException(status_code=500, detail="Failed to save profile")

@router.delete("/{company_id}", response_model=dict)
async def delete_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Delete a company profile by ID.
    """
    try:
        # Check if company exists
        company = await service.get_company_by_id(db=db, company_id=company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Delete company
        await service.delete_company(db=db, company_id=company_id)

        logger.info(
            "User %s (ID: %s) deleted company_id=%s",
            current_user.username,
            current_user.user_id,
            company_id,
        )

        return {"status": "success", "message": f"Company {company_id} deleted"}

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to delete company_id=%s by user %s (ID: %s)",
            company_id,
            current_user.username,
            current_user.user_id,
        )
        raise HTTPException(status_code=500, detail="Failed to delete company")        