import secrets
from typing import Optional

import httpx
from authlib.integrations.base_client import OAuthError
from authlib.integrations.httpx_client import AsyncOAuth2Client

from backend.app.config.logging import get_logger
from backend.app.config.settings import get_settings
from backend.app.schemas.auth import GoogleUserInfo

settings = get_settings()
oauth_config = settings.oauth2_config
logger = get_logger("oauth")

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid_configuration"


async def get_google_oauth_client() -> AsyncOAuth2Client:
    """Create and return a Google OAuth2 client"""
    logger.debug("🔗 Creating Google OAuth2 client")
    client = AsyncOAuth2Client(
        client_id=oauth_config.google_client_id,
        client_secret=oauth_config.google_client_secret,
    )
    return client


async def get_google_auth_url() -> tuple[str, str]:
    """Generate Google OAuth authorization URL and state"""
    logger.info("🚀 Generating Google OAuth2 authorization URL")
    client = await get_google_oauth_client()

    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Google OAuth2 authorization URL
    authorization_url = client.create_authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        redirect_uri=oauth_config.google_redirect_uri,
        scope="openid email profile",
        state=state,
    )

    logger.debug(f"🔗 Authorization URL generated with state: {state}")
    return authorization_url[0], state


async def get_google_user_info(code: str, state: str) -> Optional[GoogleUserInfo]:
    """Exchange authorization code for user information"""
    logger.info("👤 Processing Google OAuth callback")

    try:
        client = await get_google_oauth_client()

        # Exchange authorization code for access token
        logger.info("🔄 Exchanging authorization code for access token")
        token = await client.fetch_token(
            "https://oauth2.googleapis.com/token",
            code=code,
            redirect_uri=oauth_config.google_redirect_uri,
        )

        # Use access token to get user info
        logger.info("👤 Fetching user information from Google")
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token['access_token']}"},
            )

            if response.status_code == 200:
                user_data = response.json()
                logger.info(
                    f"✅ Successfully fetched user info for: {user_data.get('email', 'unknown')}"
                )
                return GoogleUserInfo(
                    id=user_data["id"],
                    email=user_data["email"],
                    name=user_data.get("name", ""),
                    picture=user_data.get("picture"),
                    verified_email=user_data.get("verified_email", False),
                )

        return None

    except (OAuthError, httpx.HTTPError, KeyError) as e:
        logger.error(f"❌ OAuth error: {e}")
        return None


def generate_username_from_email(email: str) -> str:
    """Generate a username from email address"""
    # Take the part before @ and remove any non-alphanumeric characters
    username = email.split("@")[0]
    username = "".join(c for c in username if c.isalnum() or c in ["_", "-"])

    # Add a random suffix to avoid collisions
    suffix = secrets.token_hex(4)
    return f"{username}_{suffix}"
