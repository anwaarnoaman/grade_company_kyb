from app.models.document import Document 
from sqlalchemy.ext.asyncio import AsyncSession 
from uuid import uuid4
from sqlalchemy import select, delete
from app.models.compnay_profile import CompanyProfile
from app.services.azure.azure_blob_service import AzureBlobService

class CompanyProfileRepository:
    def __init__(self):
        self.blob_service = AzureBlobService()

    async def create(self, db: AsyncSession, data: dict):
        obj = CompanyProfile(
            company_id=uuid4(),
            **data
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def get_all(self, db: AsyncSession) -> list[CompanyProfile]:
        """
        Fetch all company profiles from the database.
        """
        result = await db.execute(select(CompanyProfile))
        return result.scalars().all()
    
    async def get_by_id(self, db: AsyncSession, company_id: str) -> CompanyProfile | None:
        """
        Fetch a single company profile by its ID.
        """
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.company_id == company_id)
        )
        return result.scalars().first()
        
    async def update(
        self,
        db: AsyncSession,
        company_id: str,
        kyb_data: dict
    ) -> CompanyProfile | None:
        """
        Overwrite full kyb_data JSON object.
        """
        result = await db.execute(
            select(CompanyProfile).where(
                CompanyProfile.company_id == company_id
            )
        )
        company = result.scalars().first()

        if not company:
            return None

        # ✅ Replace entire JSON
        company.kyb_data = kyb_data

        await db.commit()
        await db.refresh(company)

        return company
      
    async def delete(self, db: AsyncSession, company_id: str) -> bool:
        """
        Delete a company profile by its ID.
        Deletes all related documents and their blobs first to avoid FK violation.
        """
        # 1️⃣ Fetch the company
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.company_id == company_id)
        )
        company = result.scalars().first()
        if not company:
            return False

        # 2️⃣ Fetch all documents linked to this company
        result = await db.execute(
            select(Document).where(Document.company_id == company_id)
        )
        documents = result.scalars().all()

        # 3️⃣ Delete blobs from Azure for each document
        for doc in documents:
            if doc.blob_path:  # <-- correct attribute
                try:
                    self.blob_service.delete_file(doc.blob_path)
                except Exception as e:
                    # Log the error but continue deleting
                    print(f"Failed to delete blob {doc.blob_path}: {e}")

        # 4️⃣ Delete document rows from the DB
        await db.execute(delete(Document).where(Document.company_id == company_id))

        # 5️⃣ Delete the company itself
        await db.delete(company)

        # 6️⃣ Commit all changes
        await db.commit()
        return True