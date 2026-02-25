import os
import re
from typing import Optional, Dict
from PyPDF2 import PdfReader
from dateutil import parser as date_parser
from datetime import datetime
from langdetect import detect, DetectorFactory

# Ensure consistent results
DetectorFactory.seed = 0

SUPPORTED_DOCUMENT_TYPES = {
    "TRADE LICENSE": "Trade License",
    "MEMORANDUM OF ASSOCIATION": "MOA / AOA",
    "BOARD RESOLUTION": "Board Resolution",
    "PASSPORT": "ID",
    "UAE PASSPORT": "ID",
    "BANK": "Bank Letter",
    "VAT REGISTRATION": "VAT / TRN",
    "BALANCE SHEET": "Financial Statement",
    "PROFIT & LOSS": "Financial Statement",
}


class DocumentClassificationPipeline:
    
    def extract_text(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return lang  # e.g., "en", "ar", etc.
        except:
            return "unknown"

    def classify_document(self, text: str) -> Dict:
        confidence = 0.0
        detected_type = "Unsupported"

        text_upper = text.upper()
        for keyword, doc_type in SUPPORTED_DOCUMENT_TYPES.items():
            if keyword in text_upper:
                detected_type = doc_type
                confidence += 0.5

        # Boost confidence if strong header match
        first_lines = text_upper[:300]
        for keyword in SUPPORTED_DOCUMENT_TYPES.keys():
            if keyword in first_lines:
                confidence += 0.4
                break

        confidence = min(confidence, 0.99)

        return {
            "classType": detected_type,
            "confidence": round(confidence, 2)
        }

    def extract_date(self, text: str, label_patterns: list) -> Optional[str]:
        for pattern in label_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    parsed_date = date_parser.parse(match.group(1), dayfirst=True)
                    return parsed_date.date().isoformat()
                except:
                    continue
        return None

    def extract_issue_and_expiry(self, text: str) -> Dict:
        issue_patterns = [
            r"ISSUE DATE:\s*(.+)",
            r"DATE OF ISSUE:\s*(.+)",
            r"REGISTRATION DATE:\s*(.+)"
        ]

        expiry_patterns = [
            r"EXPIRY DATE:\s*(.+)",
            r"DATE OF EXPIRY:\s*(.+)"
        ]

        issue_date = self.extract_date(text, issue_patterns)
        expiry_date = self.extract_date(text, expiry_patterns)

        return {
            "issueDate": issue_date,
            "expiryDate": expiry_date
        }

    def process_document(self, file_path: str) -> Dict:
        text = self.extract_text(file_path)

        classification = self.classify_document(text)
        dates = self.extract_issue_and_expiry(text)
        language = self.detect_language(text)

        return {
            "fileName": os.path.basename(file_path),
            "classType": classification["classType"],
            "issueDate": dates["issueDate"],
            "expiryDate": dates["expiryDate"],
            "confidence": classification["confidence"],
            "language": language,  # ✅ added language detection
            "processedAt": datetime.utcnow().isoformat()
        }
