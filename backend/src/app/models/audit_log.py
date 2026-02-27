from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_name = Column(String, nullable=True)

    action = Column(String, nullable=True)  
    # CREATE | UPDATE | DELETE

    table_name = Column(String, nullable=True)
    record_id = Column(String, nullable=True)

    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)

    message = Column(String, nullable=True)   

    created_at = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now()
    )