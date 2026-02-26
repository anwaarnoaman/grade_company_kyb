from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.compnay_profile_repository import CompanyProfileRepository
from app.models.compnay_profile import CompanyProfile
from app.core.logging import get_logger
from app.utils.misc import mask_content

logger = get_logger(__name__)

def apply_manual_edits(data: dict, edits: list[dict], company_id: str, actor: str):
    """
    Apply manual edits to nested JSON object and log all changes as audit logs.
    """
    for edit in edits:
        path = edit["fieldName"].split(".")
        obj = data
        for key in path[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]
        last_key = path[-1]

        current_value = obj.get(last_key)
        old_value = current_value
        new_value = edit["new_value"]

        if current_value != edit["old_value"]:
            logger.warning(
                f"old_value mismatch for {edit['fieldName']}: current={current_value}, expected={edit['old_value']}"
            )

        obj[last_key] = new_value

        # --- Audit log ---
        logger.info(
            f"Manual edit applied to {edit['fieldName']}",
            extra={
                "audit": True,
                "event_type": "manual_edit",
                "company_id": company_id,
                "actor": actor,
                "field_name": edit["fieldName"],
                "old_value": mask_content(str(old_value)),
                "new_value": mask_content(str(new_value)),
            },
        )

    return data

class CompanyProfileService:
    def __init__(self):
        self.repo = CompanyProfileRepository()

    async def create_company(self, db: AsyncSession, data: dict) -> CompanyProfile:
        return await self.repo.create(db=db, data=data)


    async def get_all_companies(self, db: AsyncSession) -> list[CompanyProfile]:
        """
        Service method to get all companies.
        """
        return await self.repo.get_all(db=db)

    async def get_company_by_id(self, db: AsyncSession, company_id: str) -> CompanyProfile | None:
        """
        Get a single company profile by ID.
        """
        return await self.repo.get_by_id(db=db, company_id=company_id)
    
    async def update_company_profile(
        self, db: AsyncSession, company_id: str, updated_data: dict
    ) -> CompanyProfile:
        """
        Update company profile in DB.
        """
        return await self.repo.update(db=db, company_id=company_id, data=updated_data)

    async def delete_company(self, db: AsyncSession, company_id: str) -> bool:
        """
        Delete a company profile by ID using the repository.
        Returns True if deleted, False if not found.
        """
        deleted = await self.repo.delete(db=db, company_id=company_id)
        return deleted

    async def save_manual_edits(
        self, db: AsyncSession, company_id: str, kyb_data: dict, manual_edits: list[dict], actor: str
    ) -> dict:
        """
        Apply manual edits to KYB data and save to DB.
        """
        # Apply edits
        updated_data = apply_manual_edits(
            kyb_data.get("unified_company", {}), manual_edits, company_id, actor
        )

        # Save updated data to DB
        # await self.update_company_profile(db=db, company_id=company_id, updated_data=updated_data)

        return updated_data