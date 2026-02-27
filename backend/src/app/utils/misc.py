from datetime import datetime
from typing import Optional

def str_to_date(date_str: Optional[str]) -> Optional[datetime.date]:
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str.date()
    try:
        return datetime.fromisoformat(date_str).date()
    except ValueError:
        try:
            return datetime.strptime(date_str, "%d-%m-%Y").date()
        except:
            return None
 
 
def mask_content(value: str) -> str:
    """Mask sensitive strings for audit logs"""
    if not value:
        return value
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value)-4) + value[-2:]
