 
import os
import logging
import tempfile
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.azure.azure_blob_service import AzureBlobService
from app.services.db.document_service import DocumentService
from app.services.kyb_pipeline.kyb_extraction_piepline import KYBExtractionPipeline
from app.services.kyb_pipeline.risk_engine import RiskEngine

logger = logging.getLogger(__name__)


class KYBGenerationService:
    def __init__(self):
        """
        Initialize KYB Generation Service
        """
        self.azure_service = AzureBlobService()
        self.document_service = DocumentService()
        self.extraction_pipeline = KYBExtractionPipeline()
        self.risk_engine = RiskEngine()
        self.logger = logger

    async def process(self, db: AsyncSession, company_id: str) -> Dict:
        """
        Process all documents for a company:
        1. Download files into temp folder
        2. Run KYB extraction pipeline
        3. Evaluate risk and compliance
        4. Delete all files
        5. Return unified company object
        """

        try:
            # Fetch documents (async)
            documents = await self.document_service.get_documents_by_company(db, company_id)

            if not documents:
                return {"status": "failed", "message": "No documents found for company"}

            # Create temporary folder for downloads
            with tempfile.TemporaryDirectory() as temp_dir:

                downloaded_paths: List[str] = []

                # Step 1: Download all documents
                for doc in documents:
                    blob_name = doc.blob_path
                    filename = doc.filename
                    local_path = os.path.join(temp_dir, filename)

                    self.logger.info(f"Downloading blob: {blob_name}")
                    self.azure_service.download_file(blob_name=blob_name, download_path=local_path)
                    downloaded_paths.append(local_path)
                    self.logger.info(f"Downloaded to: {local_path}")

                # Step 2: Initialize unified company object
                unified_company = {
                    "companyProfile": {},
                    "licenseDetails": {},
                    "addresses": {},
                    "shareholders": [],
                    "ubos": [],
                    "documents": [],
                    "signatories": [],
                    "financialIndicators": {},
                    "riskAssessment": {
                        "financialRiskScore": 0,
                        "riskBand": "",
                        "riskDrivers": [],
                        "confidenceLevel": ""
                    },
                    "complianceIndicators": {},
                    "missingFields": []
                }

                # Step 3: Process each PDF through extraction pipeline
               
                for file_path in downloaded_paths:
                    self.logger.info(f"Processing PDF: {file_path}")
                    self.extraction_pipeline.update_unified_object(unified_company, file_path)

                # Step 4: Run Risk Engine
                
                self.risk_engine .evaluate_financial_risk(unified_company)
                self.risk_engine .validate_documents(unified_company)

                risk_result, exceptions = self.risk_engine .finalize()
                unified_company["riskAssessment"] = risk_result
                unified_company["complianceIndicators"] = {"exceptions": exceptions}

                self.logger.info(f"KYB processing complete for company_id={company_id}")

                # Step 5: Explicitly delete all downloaded files
                for path in downloaded_paths:
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                            self.logger.info(f"Deleted file: {path}")
                        except Exception as e:
                            self.logger.warning(f"Failed to delete file {path}: {e}")

            return {"status": "success", "company_id": company_id, "unified_company": unified_company}

        except Exception as e:
            self.logger.exception("Error during KYB process")
            return {"status": "failed", "error": str(e)}