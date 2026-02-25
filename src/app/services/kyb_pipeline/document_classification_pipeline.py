import os
import re
from typing import Optional, Dict
from PyPDF2 import PdfReader
from dateutil import parser as date_parser
from datetime import datetime
from langdetect import detect, DetectorFactory
from app.core.logging import get_logger

logger = get_logger(__name__)

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


# -----------------------------
# Utility: Safe Masking
# -----------------------------
def mask_filename(name: str) -> str:
    if len(name) <= 6:
        return "***"
    return name[:3] + "***" + name[-3:]


class DocumentClassificationPipeline:

    # --------------------------------------------------
    # TEXT EXTRACTION
    # --------------------------------------------------
    def extract_text(self, file_path: str) -> str:
        logger.info(
            "PDF_TEXT_EXTRACTION_STARTED",
            extra={"file_name": mask_filename(os.path.basename(file_path))}
        )

        try:
            reader = PdfReader(file_path)
            text = ""

            for page_number, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                text += page_text + "\n"

            logger.info(
                "PDF_TEXT_EXTRACTION_COMPLETED",
                extra={
                    "file_name": mask_filename(os.path.basename(file_path)),
                    "pages": len(reader.pages),
                    "characters_extracted": len(text)
                }
            )

            return text

        except Exception as e:
            logger.error(
                "PDF_TEXT_EXTRACTION_FAILED",
                extra={
                    "file_name": mask_filename(os.path.basename(file_path)),
                    "error": str(e)
                }
            )
            raise

    # --------------------------------------------------
    # LANGUAGE DETECTION
    # --------------------------------------------------
    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)

            logger.info(
                "DOCUMENT_LANGUAGE_DETECTED",
                extra={"language": lang}
            )

            return lang

        except Exception as e:
            logger.warning(
                "LANGUAGE_DETECTION_FAILED",
                extra={"error": str(e)}
            )
            return "unknown"

    # --------------------------------------------------
    # DOCUMENT CLASSIFICATION
    # --------------------------------------------------
    def classify_document(self, text: str) -> Dict:
        confidence = 0.0
        detected_type = "Unsupported"

        text_upper = text.upper()

        for keyword, doc_type in SUPPORTED_DOCUMENT_TYPES.items():
            if keyword in text_upper:
                detected_type = doc_type
                confidence += 0.5

        # Boost confidence if keyword appears in header
        first_lines = text_upper[:300]
        for keyword in SUPPORTED_DOCUMENT_TYPES.keys():
            if keyword in first_lines:
                confidence += 0.4
                break

        confidence = min(confidence, 0.99)
        confidence = round(confidence, 2)

        logger.info(
            "DOCUMENT_CLASSIFIED",
            extra={
                "class_type": detected_type,
                "confidence": confidence
            }
        )

        # Low-confidence flag (compliance trigger)
        if confidence < 0.6:
            logger.warning(
                "LOW_CLASSIFICATION_CONFIDENCE",
                extra={
                    "class_type": detected_type,
                    "confidence": confidence,
                    "severity": "medium"
                }
            )

        # Unsupported document flag
        if detected_type == "Unsupported":
            logger.warning(
                "UNSUPPORTED_DOCUMENT_TYPE",
                extra={"severity": "medium"}
            )

        return {
            "classType": detected_type,
            "confidence": confidence
        }

    # --------------------------------------------------
    # DATE EXTRACTION
    # --------------------------------------------------
    def extract_date(self, text: str, label_patterns: list) -> Optional[str]:
        for pattern in label_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    parsed_date = date_parser.parse(match.group(1), dayfirst=True)
                    return parsed_date.date().isoformat()
                except Exception:
                    continue
        return None

    # --------------------------------------------------
    # ISSUE / EXPIRY EXTRACTION
    # --------------------------------------------------
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

        logger.info(
            "DOCUMENT_DATES_EXTRACTED",
            extra={
                "issue_date": issue_date,
                "expiry_date": expiry_date
            }
        )

        # Expiry validation
        if expiry_date:
            try:
                expiry_dt = datetime.fromisoformat(expiry_date)
                if expiry_dt.date() < datetime.utcnow().date():
                    logger.warning(
                        "DOCUMENT_EXPIRED",
                        extra={
                            "expiry_date": expiry_date,
                            "severity": "high"
                        }
                    )
            except Exception:
                logger.warning(
                    "EXPIRY_DATE_PARSE_FAILED",
                    extra={"expiry_date": expiry_date}
                )

        return {
            "issueDate": issue_date,
            "expiryDate": expiry_date
        }

    # --------------------------------------------------
    # MAIN PROCESSOR
    # --------------------------------------------------
    def process_document(self, file_path: str) -> Dict:
        file_name = os.path.basename(file_path)

        logger.info(
            "DOCUMENT_PROCESSING_STARTED",
            extra={
                "file_name": mask_filename(file_name),
                "processed_at": datetime.utcnow().isoformat()
            }
        )

        text = self.extract_text(file_path)
        classification = self.classify_document(text)
        dates = self.extract_issue_and_expiry(text)
        language = self.detect_language(text)

        result = {
            "fileName": file_name,
            "classType": classification["classType"],
            "issueDate": dates["issueDate"],
            "expiryDate": dates["expiryDate"],
            "confidence": classification["confidence"],
            "language": language,
            "processedAt": datetime.utcnow().isoformat()
        }

        logger.info(
            "DOCUMENT_PROCESSING_COMPLETED",
            extra={
                "file_name": mask_filename(file_name),
                "class_type": classification["classType"],
                "confidence": classification["confidence"],
                "language": language
            }
        )

        return result