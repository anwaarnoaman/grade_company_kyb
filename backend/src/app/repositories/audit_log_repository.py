from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.schemas.audit_log_schema import AuditLogCreate


class AuditLogRepository:

    async def create(self, db: AsyncSession, data: AuditLogCreate):
        obj = AuditLog(**data.dict())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj