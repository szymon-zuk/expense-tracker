from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.auth.jwt import verify_token
from backend.app.config.logging import get_logger
from backend.app.db.database import get_db
from backend.app.models.expenses import User

security = HTTPBearer()
logger = get_logger("auth")


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Get the current authenticated user"""

    logger.debug("🔐 Starting authentication process")

    # Check if token is provided
    if not credentials or not credentials.credentials:
        logger.warning("❌ No credentials provided in Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing. Please provide: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(
        f"🔐 Credentials received, token (first 50 chars): {credentials.credentials[:50]}..."
    )

    # Verify the token
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        logger.warning("❌ Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Please login again to get a fresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"🔐 Token verified successfully, user_id: {token_data.user_id}")

    # Get user from database
    user = db.get(User, token_data.user_id)
    if user is None:
        logger.error(f"❌ User not found in database, user_id: {token_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Token may be for a deleted user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"🔐 User found in database: {user.email}")

    # Check if user is active
    if not getattr(user, "is_active", True):
        logger.warning(f"❌ User account is not active: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled. Please contact support.",
        )

    logger.info(f"✅ Authentication successful for user: {user.email}")
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the current active user"""
    if not getattr(current_user, "is_active", True):
        logger.warning(f"❌ Inactive user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    logger.debug(f"✅ Active user verified: {current_user.email}")
    return current_user


# Convenience type annotations
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
