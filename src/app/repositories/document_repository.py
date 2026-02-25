from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document
from uuid import uuid4
from typing import List


class DocumentRepository:

    async def create(self, db: AsyncSession, data: dict):
        obj = Document(
            id=str(uuid4()),
            **data
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    

    async def get_by_company_id(self, db: AsyncSession, company_id: str) -> List[Document]:
        """
        Fetch all documents associated with a given company_id
        """
        result = await db.execute(
            select(Document).where(Document.company_id == company_id)
        )
        return result.scalars().all()