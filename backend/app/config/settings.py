import os
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


@dataclass
class JWTConfig:
    issuer: str
    secret_key: str
    algorithm: str
    access_token_ttl: timedelta
    refresh_token_ttl: timedelta


class ModeEnum(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"
    TESTING = "TESTING"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, env_file_encoding="utf-8"
    )

    MODE: ModeEnum = ModeEnum.DEVELOPMENT
    PROJECT_NAME: str = "expense-tracker"
    DEBUG: bool = True
    BASE_URL: str = "http://localhost:8000"
    API_VERSION_STR: str = "/api/v1"

    DATABASE_USERNAME: str = os.getenv("DATABASE_USERNAME")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST")
    DATABASE_PORT: int = os.getenv("DATABASE_PORT")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    @property
    def async_postgres_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            username=self.DATABASE_USERNAME,
            password=self.DATABASE_PASSWORD,
            path=self.DATABASE_NAME,
        )

    @property
    def postgres_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgres",
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            username=self.DATABASE_USERNAME,
            password=self.DATABASE_PASSWORD,
            path=self.DATABASE_NAME,
        )

    @property
    def jwt_config(self) -> JWTConfig:
        return JWTConfig(
            issuer=self.JWT_ISSUER,
            secret_key=self.JWT_SECRET_KEY,
            algorithm=self.JWT_ALGORITHM,
            access_token_ttl=timedelta(seconds=self.JWT_ACCESS_TOKEN_TTL_SECONDS),
            refresh_token_ttl=timedelta(seconds=self.JWT_REFRESH_TOKEN_TTL_SECONDS),
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings
