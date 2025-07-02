from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.config.logging import get_logger
from backend.app.config.settings import get_settings
from backend.app.schemas.auth import TokenData

settings = get_settings()
jwt_config = settings.jwt_config
logger = get_logger("jwt")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    logger.debug("🔐 Verifying password hash")
    result = pwd_context.verify(plain_password, hashed_password)
    logger.debug(f"🔐 Password verification result: {result}")
    return result


def hash_password(password: str) -> str:
    """Hash a password"""
    logger.debug("🔐 Hashing password")
    hashed = pwd_context.hash(password)
    logger.debug("🔐 Password hashed successfully")
    return hashed


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    logger.debug("🎫 Creating access token")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=jwt_config.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, jwt_config.secret_key, algorithm=jwt_config.algorithm
    )
    logger.debug(f"🎫 Access token created, expires at: {expire}")
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    logger.debug("🔄 Creating refresh token")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=jwt_config.refresh_token_expire_days
        )

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, jwt_config.secret_key, algorithm=jwt_config.algorithm
    )
    logger.debug(f"🔄 Refresh token created, expires at: {expire}")
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    logger.debug(f"🔍 Attempting to verify {token_type} token")
    logger.debug(f"🔍 Token (first 50 chars): {token[:50]}...")

    try:
        payload = jwt.decode(
            token, jwt_config.secret_key, algorithms=[jwt_config.algorithm]
        )

        logger.debug("🔍 Token decoded successfully")
        logger.debug(f"🔍 Token payload keys: {list(payload.keys())}")

        # Check token type
        token_type_in_payload = payload.get("type")
        logger.debug(f"🔍 Token type in payload: {token_type_in_payload}")

        if token_type_in_payload != token_type:
            logger.warning(
                f"❌ Token type mismatch. Expected: {token_type}, Got: {token_type_in_payload}"
            )
            return None

        user_id_str = payload.get("sub")
        email = payload.get("email")

        logger.debug(f"🔍 Extracted user_id_str: {user_id_str}, email: {email}")

        if user_id_str is None:
            logger.error("❌ user_id_str is None in token payload")
            return None

        if email is None:
            logger.error("❌ email is None in token payload")
            return None

        # Convert string user_id back to integer
        try:
            user_id = int(user_id_str)
            logger.debug(f"🔍 Converted user_id to int: {user_id}")
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Failed to convert user_id to int: {e}")
            return None

        logger.debug("✅ Token verification successful")
        return TokenData(user_id=user_id, email=email)
    except JWTError as e:
        logger.error(f"❌ JWT verification failed: {str(e)}")
        logger.debug(f"❌ JWT error type: {type(e).__name__}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error during token verification: {str(e)}")
        logger.debug(f"❌ Exception type: {type(e).__name__}")
        return None


def create_token_pair(user_id: int, email: str) -> dict:
    """Create both access and refresh tokens for a user"""
    logger.info(f"🎫 Creating token pair for user: {email}")

    # Convert user_id to string as JWT 'sub' claim must be a string
    access_token = create_access_token(data={"sub": str(user_id), "email": email})
    refresh_token = create_refresh_token(data={"sub": str(user_id), "email": email})

    token_pair = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": jwt_config.access_token_expire_minutes * 60,  # in seconds
    }

    logger.info(f"🎫 Token pair created successfully for user: {email}")
    return token_pair
