from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    model_config = SettingsConfigDict(case_sensitive=True)

    MODE: ModeEnum = ModeEnum.DEVELOPMENT
    PROJECT_NAME: str = "expense-tracker"
    DEBUG: bool = True
    BASE_URL: str = "http://localhost:8000"
    API_VERSION_STR: str = "/api/v1"

    DATABASE_USERNAME: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "expense_tracker_db"
    DATABASE_URL: str = (
        "postgresql://postgres:postgres@localhost:5432/expense_tracker_db"
    )

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

    # @property
    # def jwt_config(self) -> JWTConfig:
    #     return JWTConfig(
    #         issuer=self.JWT_ISSUER,
    #         secret_key=self.JWT_SECRET_KEY,
    #         algorithm=self.JWT_ALGORITHM,
    #         access_token_ttl=timedelta(seconds=self.JWT_ACCESS_TOKEN_TTL_SECONDS),
    #         refresh_token_ttl=timedelta(seconds=self.JWT_REFRESH_TOKEN_TTL_SECONDS),
    #     )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings
