from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.repositories.document_repository import DocumentRepository
from app.models.document import Document

class DocumentService:
    def __init__(self):
        self.repo = DocumentRepository()

    async def upload_documents(self, db: AsyncSession, data_list: list) -> List[Document]:
        created_docs = []
        for data in data_list:
            doc = await self.repo.create(db=db, data=data)
            created_docs.append(doc)
        return created_docs

    async def get_documents_by_company(self, db: AsyncSession, company_id: str) -> List[Document]:
        return await self.repo.get_by_company_id(db=db, company_id=company_id)