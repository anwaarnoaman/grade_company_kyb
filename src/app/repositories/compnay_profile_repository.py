from sqlalchemy.ext.asyncio import AsyncSession 
from uuid import uuid4

from app.models.compnay_profile import CompanyProfile

class CompanyProfileRepository:

    async def create(self, db: AsyncSession, data: dict):
        obj = CompanyProfile(
            company_id=uuid4(),
            **data
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj