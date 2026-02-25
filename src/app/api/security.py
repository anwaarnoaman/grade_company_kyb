from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.logging import get_logger
from app.core.security_utils import create_access_token
from app.services.db.auth_service import authenticate_user  # import from service

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

# Login endpoint
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint to authenticate a user and generate JWT token.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    access_token_expires = timedelta(minutes=60)
    token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    logger.info(f"User {user['username']} logged in successfully")
    return {"access_token": token, "token_type": "bearer"}