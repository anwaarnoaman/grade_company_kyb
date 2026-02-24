from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dummy users database
fake_users_db = {
    "admin": {
        "id": 1,
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"[:72])
    },
    "noaman": {
        "id": 2,
        "username": "noaman",
        "hashed_password": pwd_context.hash("noaman123"[:72])
    },
}

def authenticate_user(username: str, password: str):
    """
    Verify the username and password.
    Returns the user dict if authenticated, otherwise None.
    """
    user = fake_users_db.get(username)
    if not user:
        return None
    if not pwd_context.verify(password, user["hashed_password"]):
        return None
    return user