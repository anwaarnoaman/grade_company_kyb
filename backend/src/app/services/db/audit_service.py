from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log_schema import AuditLogCreate


async def log_audit(
    db: AsyncSession,
    company_id=None,
    user_name=None,
    action=None,
    table_name=None,
    record_id=None,
    old_value=None,
    new_value=None,
    message=None,  
):
    repo = AuditLogRepository()

    audit = AuditLogCreate(
        company_id=company_id,
        user_name=user_name,
        action=action,
        table_name=table_name,
        record_id=str(record_id) if record_id else None,
        old_value=old_value,
        new_value=new_value,
        message=message,   
    )

    await repo.create(db, audit)