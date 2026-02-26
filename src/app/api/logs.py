from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime
import json

from app.core.auth_dependencies import get_current_user
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/logs", tags=["Logs"])

LOGS_DIR = Path.cwd() / "logs"
ALLOWED_LOG_FILES = {"error.log", "info.log", "warning.log", "kyb_audit.log"}

@router.get("", response_class=JSONResponse)
def get_logs(
    file_name: str = Query("info.log", description="Log file to read"),
    company_id: str | None = Query(None, description="Filter by company ID"),
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    current_user=Depends(get_current_user)
):
    """
    Read log file contents from the logs folder and filter by company ID and date range.
    """
    if file_name not in ALLOWED_LOG_FILES:
        raise HTTPException(status_code=400, detail=f"Log file '{file_name}' is not allowed.")

    log_file_path = LOGS_DIR / file_name

    if not log_file_path.exists() or not log_file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Log file '{file_name}' not found.")

    logger.info(f"User {current_user.username} accessed log file: {file_name}")

    # Parse date filters
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    filtered_logs = []

    with log_file_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                log_entry = json.loads(line)
            except json.JSONDecodeError:
                continue  # skip invalid lines

            # Filter by company ID
            log_company_id = log_entry.get("companyId")
            if company_id:
                if isinstance(log_company_id, list):
                    if company_id not in log_company_id:
                        continue
                elif log_company_id != company_id:
                    continue

            # Filter by date
            log_timestamp = log_entry.get("timestamp")
            if log_timestamp:
                log_dt = datetime.fromisoformat(log_timestamp)
                if start_dt and log_dt < start_dt:
                    continue
                if end_dt and log_dt > end_dt:
                    continue

            filtered_logs.append(log_entry)

    return {"count": len(filtered_logs), "logs": filtered_logs}