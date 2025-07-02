from datetime import datetime, timezone
from typing import Annotated

from fastapi import (APIRouter, Depends, HTTPException, Request, Response,
                     status)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import CurrentUser
from backend.app.auth.jwt import (create_token_pair, hash_password,
                                  verify_password, verify_token)
from backend.app.auth.oauth import get_google_auth_url, get_google_user_info
from backend.app.config.logging import get_logger
from backend.app.db.database import get_db
from backend.app.models.expenses import User
from backend.app.schemas.auth import (LoginRequest, RefreshTokenRequest, Token,
                                      UserCreate, UserResponse)

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger("auth.router")


@router.get("/help")
def auth_help():
    """Get help with authentication - shows proper token format and common issues"""
    logger.info("📚 Authentication help endpoint accessed")
    return {
        "message": "Authentication Help",
        "token_format": {
            "correct": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "incorrect": "Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "note": "The word 'Bearer' followed by a space is required!",
        },
        "steps": {
            "1": "Register: POST /auth/register",
            "2": "Login: POST /auth/login",
            "3": "Copy the access_token from login response",
            "4": "Use format: Authorization: Bearer <access_token>",
            "5": "Test with: GET /auth/me or GET /auth/token-info",
        },
        "common_issues": {
            "could_not_validate_credentials": "Missing 'Bearer ' prefix or invalid token",
            "unauthorized": "Token expired (30 min) or wrong format",
            "forbidden": "User account disabled",
        },
        "tools": {
            "swagger_ui": "http://localhost:8000/docs - Use 'Authorize' button",
            "token_test": "GET /auth/token-info - Test if your token works",
            "user_info": "GET /auth/me - Get your user information",
        },
    }


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password",
)
def register(user_data: UserCreate, db: Annotated[Session, Depends(get_db)]):
    """Register a new user"""
    logger.info(f"👤 User registration attempt for email: {user_data.email}")

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(
            f"❌ Registration failed - user already exists: {user_data.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        provider="local",
        is_active=True,
        is_verified=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"✅ User registered successfully: {user_data.email}")
    return UserResponse.model_validate(new_user)


@router.post(
    "/login",
    response_model=Token,
    summary="Login user",
    description="Authenticate user with email and password, returns JWT tokens",
)
def login(login_data: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    """Authenticate user and return JWT tokens"""
    logger.info(f"🔐 Login attempt for email: {login_data.email}")

    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        logger.warning(f"❌ Login failed - user not found: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not user.hashed_password or not verify_password(
        login_data.password, user.hashed_password
    ):
        logger.warning(f"❌ Login failed - invalid password: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create token pair
    token_data = create_token_pair(user.id, user.email)

    # Add usage instructions to the response
    response_data = Token(**token_data)

    logger.info(f"✅ User logged in successfully: {login_data.email}")
    return {
        **response_data.model_dump(),
        "usage_example": "Authorization: Bearer "
        + token_data["access_token"][:50]
        + "...",
        "instructions": "Use this token in Authorization header as: Bearer <access_token>",
    }


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get a new access token using refresh token",
)
def refresh_token(
    refresh_data: RefreshTokenRequest, db: Annotated[Session, Depends(get_db)]
):
    """Refresh access token using refresh token"""
    logger.info("🔄 Token refresh attempt")

    # Verify refresh token
    token_data = verify_token(refresh_data.refresh_token, token_type="refresh")
    if token_data is None:
        logger.warning("❌ Token refresh failed - invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Get user from database
    user = db.get(User, token_data.user_id)
    if user is None:
        logger.error(f"❌ Token refresh failed - user not found: {token_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Create new token pair
    new_token_data = create_token_pair(user.id, user.email)

    # Add usage instructions to the response
    response_data = Token(**new_token_data)

    logger.info(f"✅ Token refreshed successfully for user: {user.email}")
    return {
        **response_data.model_dump(),
        "usage_example": "Authorization: Bearer "
        + new_token_data["access_token"][:50]
        + "...",
        "instructions": "Use this token in Authorization header as: Bearer <access_token>",
        "message": "Token refreshed successfully!",
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user",
)
def get_current_user_info(current_user: CurrentUser):
    """Get current user information"""
    logger.info(f"👤 User info requested for: {current_user.email}")
    return UserResponse.model_validate(current_user)


@router.get("/google")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    logger.info("🔗 Google OAuth authentication initiated")

    try:
        auth_url, state = await get_google_auth_url()

        # Store state in session for CSRF protection
        request.session["oauth_state"] = state

        logger.debug(f"🔗 OAuth state stored: {state}")
        return {"authorization_url": auth_url, "state": state}

    except Exception as e:
        logger.error(f"❌ Failed to initiate Google OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Google OAuth",
        )


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = None,
    state: str = None,
    db: Session = Depends(get_db),
):
    """Handle Google OAuth callback"""
    logger.info("🔗 Google OAuth callback received")

    if not code:
        logger.warning("❌ Google OAuth callback failed - no authorization code")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided",
        )

    # Verify state for CSRF protection
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        logger.warning("❌ Google OAuth callback failed - invalid state parameter")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter"
        )

    # Clear the state from session
    request.session.pop("oauth_state", None)

    # Get user info from Google
    google_user = await get_google_user_info(code, state)
    if not google_user:
        logger.warning(
            "❌ Google OAuth callback failed - failed to get user information from Google"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information from Google",
        )

    # Check if user exists, create if not
    user = db.query(User).filter(User.email == google_user.email).first()
    if not user:
        # Create new user from Google info
        user = User(
            email=google_user.email,
            username=google_user.email.split("@")[0],  # Simple username generation
            full_name=google_user.name,
            google_id=google_user.id,
            provider="google",
            avatar_url=google_user.picture,
            is_active=True,
            is_verified=google_user.verified_email,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✅ New user created from Google OAuth: {google_user.email}")
    else:
        # Update existing user with Google info if needed
        if not user.google_id:
            user.google_id = google_user.id
            user.provider = "google"
            user.avatar_url = google_user.picture
            user.is_verified = google_user.verified_email
            db.commit()
            logger.info(
                f"✅ Existing user linked with Google OAuth: {google_user.email}"
            )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create token pair
    token_data = create_token_pair(user.id, user.email)

    # Add usage instructions to the response
    response_data = Token(**token_data)
    logger.info(
        f"✅ Google OAuth callback processed successfully for user: {user.email}"
    )
    return {
        **response_data.model_dump(),
        "usage_example": "Authorization: Bearer "
        + token_data["access_token"][:50]
        + "...",
        "instructions": "Use this token in Authorization header as: Bearer <access_token>",
        "provider": "google",
        "message": "Successfully authenticated with Google!",
    }


@router.post("/logout")
def logout(current_user: CurrentUser):
    """Logout user (client should delete the token)"""
    logger.info(f"👋 User logout: {current_user.email}")
    # In a more complete implementation, you might want to:
    # - Add token to a blacklist
    # - Store active sessions in a database
    # For now, we just return a success message as the client handles token deletion
    return {"message": "Successfully logged out"}


@router.get("/token-info")
def token_info(current_user: CurrentUser):
    """Get information about the current token and user - useful for debugging"""
    logger.debug(f"🔍 Token info requested for user: {current_user.email}")
    return {
        "message": "Token is valid!",
        "user_id": current_user.id,
        "email": current_user.email,
        "provider": current_user.provider,
        "is_active": getattr(current_user, "is_active", True),
        "token_format_example": "Authorization: Bearer <your_access_token_here>",
        "instructions": {
            "curl": "curl -H 'Authorization: Bearer YOUR_TOKEN' http://localhost:8000/auth/me",
            "swagger": "Click 'Authorize' button and enter: Bearer YOUR_TOKEN",
            "postman": "Set Authorization Type to 'Bearer Token' and paste your token",
        },
    }
