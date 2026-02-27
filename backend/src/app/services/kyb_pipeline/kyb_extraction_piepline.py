import os
import re
from typing import Dict, List, Optional
from PyPDF2 import PdfReader
from dateutil import parser as date_parser
from datetime import datetime
import json

# =========================================================
# Utility: Standard Field Builder (Traceable & Auditable)
# =========================================================

def build_field(value, source, confidence, method="regex_v1"):
    return {
        "value": value,
        "sourceDocument": source,
        "confidence": round(confidence, 2),
        "extractionMethod": method
    }

# =========================================================
# Document Processor
# =========================================================

class KYBExtractionPipeline:

    SUPPORTED_TYPES = {
        "TRADE LICENSE": "Trade License",
        "MEMORANDUM OF ASSOCIATION": "MOA / AOA",
        "BOARD RESOLUTION": "Board Resolution",
        "PASSPORT": "ID",
        "BANK": "Bank Letter",
        "VAT REGISTRATION": "VAT / TRN",
        "BALANCE SHEET": "Balance Sheet",
        "PROFIT & LOSS": "Profit & Loss"
    }

    def __init__(self):
        pass

    # -------------------------
    # TEXT EXTRACTION
    # -------------------------

    def extract_text(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.upper()

    # -------------------------
    # CLASSIFICATION
    # -------------------------

    def classify_document(self, text: str) -> Dict:
        confidence = 0.0
        doc_type = "Unsupported"

        for keyword, dtype in self.SUPPORTED_TYPES.items():
            if keyword in text:
                doc_type = dtype
                confidence += 0.6

        if doc_type != "Unsupported":
            confidence += 0.3

        return {
            "classType": doc_type,
            "confidence": min(round(confidence, 2), 0.99)
        }

    # -------------------------
    # DATE EXTRACTION
    # -------------------------

    def extract_date(self, text: str, patterns: List[str]) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return date_parser.parse(match.group(1)).date().isoformat()
                except:
                    continue
        return None

    def extract_issue_expiry(self, text: str):
        issue_patterns = [
            r"ISSUE DATE:\s*(.+)",
            r"DATE OF ISSUE:\s*(.+)",
            r"REGISTRATION DATE:\s*(.+)"
        ]
        expiry_patterns = [
            r"EXPIRY DATE:\s*(.+)",
            r"DATE OF EXPIRY:\s*(.+)"
        ]

        return {
            "issueDate": self.extract_date(text, issue_patterns),
            "expiryDate": self.extract_date(text, expiry_patterns)
        }

    # -------------------------
    # FIELD EXTRACTIONS
    # -------------------------

    def extract_company_profile(self, text, file):
        profile = {}
        # Only non-license company info
        patterns = {
            "legalName": r"COMPANY NAME:\s*(.+)",
            "legalForm": r"LEGAL FORM:\s*(.+)"
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                profile[field] = build_field(match.group(1).strip(), file, 0.95)
        return profile


    def extract_license_details(self, text, file):
        license_info = {}
        patterns = {
            "registrationNumber": r"LICENSE NUMBER:\s*(.+)",
            "jurisdiction": r"JURISDICTION:\s*(.+)",
            "licenseIssuingAuthority": r"ISSUING AUTHORITY:\s*(.+)",
            "issueDate": r"ISSUE DATE:\s*(.+)",
            "expiryDate": r"EXPIRY DATE:\s*(.+)"
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                # For dates, parse to ISO format if possible
                if "Date" in field:
                    try:
                        license_info[field] = build_field(date_parser.parse(match.group(1)).date().isoformat(), file, 0.95)
                    except:
                        license_info[field] = build_field(match.group(1).strip(), file, 0.8)
                else:
                    license_info[field] = build_field(match.group(1).strip(), file, 0.95)
        return license_info

    def extract_shareholders(self, text, file):
        shareholders = []
        matches = re.findall(r"-\s*(.+?):\s*(\d+)%", text)
        for name, pct in matches:
            shareholders.append({
                "name": build_field(name.strip(), file, 0.9),
                "ownershipPercentage": build_field(float(pct), file, 0.9),
                "controlType": build_field("Direct", file, 0.8)
            })
        return shareholders

    def extract_signatories(self, text, file):
        signatories = []
        matches = re.findall(r"MR\.?\s*(.+?),\s*(CEO|CFO|DIRECTOR)", text)
        for name, role in matches:
            signatories.append({
                "name": build_field(name.strip(), file, 0.85),
                "role": build_field(role.strip(), file, 0.85),
                "authoritySource": build_field("Board Resolution", file, 0.8)
            })
        return signatories

    def extract_financials(self, text, file, doc_type=None):
        financials = {}
        
        if doc_type == "Balance Sheet":
            patterns = {
                "totalAssets": r"TOTAL ASSETS:\s*(-?[\d,]+)",
                "totalLiabilities": r"TOTAL LIABILITIES:\s*(-?[\d,]+)"
            }
        elif doc_type == "Profit & Loss":
            patterns = {
                "revenue": r"REVENUE:\s*(-?[\d,]+)",
                "netProfit": r"NET PROFIT:\s*(-?[\d,]+)"
            }
        else:
            # fallback: try all numeric patterns
            patterns = {
                "revenue": r"REVENUE:\s*(-?[\d,]+)",
                "netProfit": r"NET PROFIT:\s*(-?[\d,]+)",
                "totalAssets": r"TOTAL ASSETS:\s*(-?[\d,]+)",
                "totalLiabilities": r"TOTAL LIABILITIES:\s*(-?[\d,]+)"
            }

        for field, pattern in patterns.items():
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                # Remove commas and convert to float
                value = float(match.group(1).replace(",", ""))
                financials[field] = build_field(value, file, 0.95)
        
        # Optional audit and FY period
        audit = re.search(r"AUDIT STATUS:\s*(.+)", text)
        if audit:
            financials["auditStatus"] = build_field(audit.group(1).strip(), file, 0.9)
        period = re.search(r"FY\s*(\d{4})", text)
        if period:
            financials["financialPeriod"] = build_field(period.group(1), file, 0.85)

        return financials

    # -------------------------
    # SINGLE FILE UPDATE
    # -------------------------

    def update_unified_object(self, unified: Dict, file_path: str) -> None:
            file_name = os.path.basename(file_path)
            text = self.extract_text(file_path)
            classification = self.classify_document(text)
            dates = self.extract_issue_expiry(text)

            # Append document metadata
            unified["documents"].append({
                "fileName": file_name,
                "classType": classification["classType"],
                "confidence": classification["confidence"],
                "issueDate": dates["issueDate"],
                "expiryDate": dates["expiryDate"],
                "processedAt": datetime.utcnow().isoformat()
            })

            # Update companyProfile (non-license fields)
            unified["companyProfile"].update(self.extract_company_profile(text, file_name))

            # Update license details separately
            unified["licenseDetails"].update(self.extract_license_details(text, file_name))

            # Other extractions
            unified["shareholders"].extend(self.extract_shareholders(text, file_name))
            unified["signatories"].extend(self.extract_signatories(text, file_name))
            financial_data = self.extract_financials(text, file_name, doc_type=classification["classType"])
            unified["financialIndicators"].update(financial_data)
            # Detect missing fields dynamically
            self.detect_missing_fields(unified)

    # -------------------------
    # MISSING FIELD DETECTION
    # -------------------------

    def detect_missing_fields(self, output):
        required_profile = ["legalName", "registrationNumber", "jurisdiction"]
        required_financials = ["totalAssets", "totalLiabilities","revenue","netProfit"]

        # Reset missing fields each time
        output["missingFields"] = []

        for field in required_profile:
            if field not in output["companyProfile"]:
                output["missingFields"].append(field)
        for field in required_financials:
            if field not in output["financialIndicators"]:
                output["missingFields"].append(field)
