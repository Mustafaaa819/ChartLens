from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ANTHROPIC_API_KEY: str
    SECRET_KEY: str
    DATABASE_URL: str = "sqlite:///./chartlens.db"
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_PAGES_MVP: int = 500
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    LEMONSQUEEZY_API_KEY: str = ""
    LEMONSQUEEZY_STORE_ID: str = ""
    LEMONSQUEEZY_VARIANT_ID: str = ""
    LEMONSQUEEZY_WEBHOOK_SECRET: str = ""
    APP_ENV: str = "development"

    @property
    def is_production(self) -> bool:
        """Return True when APP_ENV is set to 'production'."""
        return self.APP_ENV.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance — loaded once, reused everywhere."""
    return Settings()
