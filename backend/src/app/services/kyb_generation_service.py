import os
import logging
import tempfile
from typing import Dict, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.azure.azure_blob_service import AzureBlobService
from app.services.db.document_service import DocumentService
from app.services.kyb_pipeline.kyb_extraction_piepline import KYBExtractionPipeline
from app.services.kyb_pipeline.risk_engine import RiskEngine

logger = logging.getLogger(__name__)

 
class KYBGenerationService:
    def __init__(self):
        self.azure_service = AzureBlobService()
        self.document_service = DocumentService()
        self.extraction_pipeline = KYBExtractionPipeline()
        self.risk_engine = RiskEngine()
        self.logger = logger

        self.MANDATORY_DOCS = {
            "Trade License",
            "MOA / AOA",
            "ID",
            "Balance Sheet",
            "Profit & Loss"
        }

        self.SUPPORTED_DOCS = {
            "Trade License",
            "MOA / AOA",
            "Board Resolution",
            "ID",
            "Bank Letter",
            "VAT / TRN",
            "Balance Sheet",
            "Profit & Loss"
        }

    async def process(self, db: AsyncSession, company_id: str) -> Dict:

        try:
            documents = await self.document_service.get_documents_by_company(db, company_id)

            if not documents:
                logger.warning(
                    "KYB_NO_DOCUMENTS_FOUND",
                    extra={"audit": True, "company_id": (company_id)}
                )
                return {"status": "failed", "message": "No documents found for company"}

            with tempfile.TemporaryDirectory() as temp_dir:

                downloaded_paths: List[str] = []

                # Step 1: Download all documents
                for doc in documents:
                    blob_name = doc.blob_path
                    filename = doc.filename
                    local_path = os.path.join(temp_dir, filename)

 
                    self.azure_service.download_file(blob_name=blob_name, download_path=local_path)
                    downloaded_paths.append(local_path)

 

                # Step 2: Initialize unified object
                unified_company = {
                    "companyProfile": {},
                    "licenseDetails": {},
                    "addresses": {},
                    "shareholders": [],
                    "ubos": [],
                    "documents": [],
                    "signatories": [],
                    "financialIndicators": {},
                    "riskAssessment": None,
                    "complianceIndicators": {"exceptions": []},
                    "missingFields": []
                }

                # Step 3: Extraction
                for file_path in downloaded_paths:
                    self.extraction_pipeline.update_unified_object(unified_company, file_path)

 
                # Step 4A: Compliance Validation
                exceptions = []
                missing_fields = []
                uploaded_types = {doc["classType"] for doc in unified_company["documents"]}

                # Missing mandatory documents
                missing_docs = self.MANDATORY_DOCS - uploaded_types
                for doc_type in missing_docs:
                    exceptions.append({
                        "type": "Missing Document",
                        "message": f"{doc_type} not provided",
                        "severity": "High",
                        "impactedFields": ["documents"],
                        "requiredAction": "Request document from client"
                    })
                    missing_fields.append(f"documents.{doc_type}")
                # ----------------- AUDIT LOG FOR MISSING DOCUMENTS -----------------
                if missing_docs:
                    logger.warning(
                        "MISSING_DOCUMENTS_DETECTED",
                        extra={
                            "audit": True,
                            "company_id": (company_id),
                            "missing_documents": ", ".join(missing_docs)
                        }
                    )
                # Unsupported document types
                for doc in unified_company["documents"]:
                    if doc["classType"] not in self.SUPPORTED_DOCS:
                        exceptions.append({
                            "type": "Unsupported Document",
                            "message": f"{doc['classType']} is not supported",
                            "severity": "Medium",
                            "impactedFields": ["documents"],
                            "requiredAction": "Manual compliance review"
                        })

                # Expired documents
                today = datetime.utcnow().date()
                for doc in unified_company["documents"]:
                    expiry = doc.get("expiryDate")
                    if expiry:
                        try:
                            expiry_date = datetime.fromisoformat(expiry).date()
                            if expiry_date < today:
                                exceptions.append({
                                    "type": "Expired Document",
                                    "message": f"{(doc['fileName'])} is expired",
                                    "severity": "High",
                                    "impactedFields": ["documents.expiryDate"],
                                    "requiredAction": "Request renewed document"
                                })
                        except Exception:
                            logger.warning(
                                "EXPIRY_DATE_PARSE_FAILED",
                                extra={
                                    "audit": True,
                                    "company_id": (company_id),
                                    "doc_name": (doc["fileName"])
                                }
                            )

                unified_company["complianceIndicators"]["exceptions"] = exceptions
                unified_company["missingFields"] = missing_fields

                # Audit log: compliance summary
                logger.info(
                    "COMPLIANCE_VALIDATION_COMPLETE",
                    extra={
                        "audit": True,
                        "company_id": (company_id),
                        "missing_documents": None,
                        "compliance_exceptions_count": len(exceptions)
                    }
                )

                # Step 4B: Financial Risk Scoring
                self.risk_engine.reset()
                self.risk_engine.evaluate_financial_risk(unified_company)
                risk_result, exceptions = self.risk_engine.finalize()
                unified_company["riskAssessment"] = risk_result

 
                # Audit log: KYB process complete
                logger.info(
                    "KYB_PROCESS_COMPLETE",
                    extra={"audit": True, "company_id": (company_id)}
                )

                # Cleanup
                for path in downloaded_paths:
                    if os.path.exists(path):
                        os.remove(path)

            return {
                "status": "success",
                "company_id": company_id,
                "unified_company": unified_company
            }

        except Exception as e:
            logger.exception(
                "KYB_PROCESS_ERROR",
                extra={"audit": True, "company_id": (company_id)}
            )
            return {"status": "failed", "error": str(e)}