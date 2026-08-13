from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/music_db"

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me"

    SECRET_KEY: str = "change-this-secret-key"
    APP_ENV: str = "development"

    CORS_ORIGINS: list[str] = [
        "https://deluxesalonsongs.com",
        "https://www.deluxesalonsongs.com",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
