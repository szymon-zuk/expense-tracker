from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class JWTConfig:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int


@dataclass
class OAuth2Config:
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str


class ModeEnum(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"
    TESTING = "TESTING"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    MODE: ModeEnum = ModeEnum.DEVELOPMENT
    PROJECT_NAME: str = "expense-tracker"
    DEBUG: bool = True
    BASE_URL: str = "http://localhost:8000"
    API_VERSION_STR: str = "/api/v1"

    # Database Configuration
    DATABASE_USERNAME: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "expense_tracker_db"
    DATABASE_URL: str = (
        "postgresql://postgres:postgres@localhost:5432/expense_tracker_db"
    )

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OAuth2 Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    @property
    def postgres_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            username=self.DATABASE_USERNAME,
            password=self.DATABASE_PASSWORD,
            path=self.DATABASE_NAME,
        )

    @property
    def jwt_config(self) -> JWTConfig:
        return JWTConfig(
            secret_key=self.JWT_SECRET_KEY,
            algorithm=self.JWT_ALGORITHM,
            access_token_expire_minutes=self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_token_expire_days=self.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        )

    @property
    def oauth2_config(self) -> OAuth2Config:
        return OAuth2Config(
            google_client_id=self.GOOGLE_CLIENT_ID,
            google_client_secret=self.GOOGLE_CLIENT_SECRET,
            google_redirect_uri=self.GOOGLE_REDIRECT_URI,
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings
