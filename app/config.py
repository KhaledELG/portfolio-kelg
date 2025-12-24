"""Application configuration using pydantic settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Portfolio"
    environment: str = "development"
    port: int = 8000
    github_username: str = "KhaledELG"
    github_token: str | None = None
    cache_ttl_seconds: int = 900
    default_locale: str = "en"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
