import logging
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# =========================
# Filters
# =========================

class LevelFilter(logging.Filter):
    """Filter logs by exact level (INFO includes DEBUG+INFO)."""

    def __init__(self, level: int):
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        # Don't send audit logs to normal log files
        if getattr(record, "audit", False):
            return False

        if self.level == logging.INFO:
            return record.levelno <= logging.INFO
        return record.levelno == self.level


class AuditFilter(logging.Filter):
    """Allow only audit logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        return getattr(record, "audit", False)


# =========================
# JSON Formatter for Audit
# =========================

class JSONAuditFormatter(logging.Formatter):
    """Structured JSON formatter for audit logs."""

    def format(self, record: logging.LogRecord) -> str:
        # Standard audit fields
        audit_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "eventType": getattr(record, "event_type", None),
                "companyId": getattr(record, "company_id", None),
                "correlationId": getattr(record, "correlation_id", None),
                "actor": getattr(record, "actor", "system"),

                # Manual edit / field-specific info
                "field_name": getattr(record, "field_name", None),
                "old_value": getattr(record, "old_value", None),
                "new_value": getattr(record, "new_value", None),

                # Document-specific fields
                "doc_name": getattr(record, "doc_name", None),
                "class_type": getattr(record, "class_type", None),
                "confidence": getattr(record, "confidence", None),
                "uploader": getattr(record, "uploader", None),
                "blob_path": getattr(record, "blob_path", None),
                "issue_date": getattr(record, "issue_date", None),
                "expiry_date": getattr(record, "expiry_date", None),
                "language": getattr(record, "language", None),

                # KYB-specific / audit tracking
                "missing_documents": getattr(record, "missing_documents", None),
                "step": getattr(record, "step", None),             
                "document_id": getattr(record, "document_id", None),
                "kyb_section": getattr(record, "kyb_section", None), 
                "notes": getattr(record, "notes", None),          
            }

        # Remove None values to keep JSON clean
        audit_log = {k: v for k, v in audit_log.items() if v is not None}

        return json.dumps(audit_log)


# =========================
# Setup Logging
# =========================

def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handlers: list[logging.Handler] = []

    # ---- Console handler ----
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handlers.append(console_handler)

    if settings.log_to_file:
        log_dir = Path(settings.log_file_path)
        log_dir.parent.mkdir(parents=True, exist_ok=True)

        # ---- Info + Debug ----
        info_handler = RotatingFileHandler(
            filename=log_dir.parent / "info.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        info_handler.setLevel(logging.DEBUG)
        info_handler.addFilter(LevelFilter(logging.INFO))
        info_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(info_handler)

        # ---- Warning ----
        warning_handler = RotatingFileHandler(
            filename=log_dir.parent / "warning.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        warning_handler.setLevel(logging.WARNING)
        warning_handler.addFilter(LevelFilter(logging.WARNING))
        warning_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(warning_handler)

        # ---- Error ----
        error_handler = RotatingFileHandler(
            filename=log_dir.parent / "error.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(LevelFilter(logging.ERROR))
        error_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(error_handler)

        # ---- KYB Audit log ----
        audit_handler = RotatingFileHandler(
            filename=log_dir.parent / "kyb_audit.log",
            maxBytes=20 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.addFilter(AuditFilter())
        audit_handler.setFormatter(JSONAuditFormatter())
        handlers.append(audit_handler)

    logging.basicConfig(
        level=log_level,
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)