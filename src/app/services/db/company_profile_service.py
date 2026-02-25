from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.compnay_profile_repository import CompanyProfileRepository
from app.models.compnay_profile import CompanyProfile

class CompanyProfileService:
    def __init__(self):
        self.repo = CompanyProfileRepository()

    async def create_company(self, db: AsyncSession, data: dict) -> CompanyProfile:
        return await self.repo.create(db=db, data=data)