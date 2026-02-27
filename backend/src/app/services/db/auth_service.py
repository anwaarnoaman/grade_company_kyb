from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.db.audit_service import log_audit
# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dummy users database
fake_users_db = {
    "admin": {
        "id": 1,
        "username": "admin",
        "company_id": None,  # add if available
        "hashed_password": pwd_context.hash("admin123"[:72])
    },
    "noaman": {
        "id": 2,
        "username": "noaman",
        "company_id": None,
        "hashed_password": pwd_context.hash("noaman123"[:72])
    },
}


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
):
 
    user = fake_users_db.get(username)
    if not user:
        return None
    if not pwd_context.verify(password, user["hashed_password"]):
        return None
    
    await log_audit(
        db=db,
        company_id=user.get("company_id"),
        user_name=user["username"],
        action="LOGIN",
        table_name="users",
        record_id=str(user["id"]),
        old_value=None,
        new_value=None,
        message=f"User {user['username']} logged in successfully",
    )
    return user