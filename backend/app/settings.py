"""Application settings and configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_env: str = "dev"
    requesting_bank_id: str = "team200"

    # Bank URLs
    vbank_base_url: str = "https://vbank.open.bankingapi.ru"
    abank_base_url: str = "https://abank.open.bankingapi.ru"
    sbank_base_url: str = "https://sbank.open.bankingapi.ru"

    # Bank credentials
    vbank_client_id: str = ""
    vbank_client_secret: str = ""
    abank_client_id: str = ""
    abank_client_secret: str = ""
    sbank_client_id: str = ""
    sbank_client_secret: str = ""

    # HTTP settings
    http_timeout_seconds: int = 15
    cache_ttl_seconds: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

