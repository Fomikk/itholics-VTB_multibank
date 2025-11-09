"""HTTP client for ABank API."""
from app.core.base_client import BaseBankClient
from app.settings import settings


class ABankClient(BaseBankClient):
    """HTTP client for ABank API."""

    def __init__(self):
        """Initialize ABank client with settings."""
        super().__init__(
            base_url=settings.abank_base_url,
            client_id=settings.abank_client_id,
            client_secret=settings.abank_client_secret,
            bank_code="abank",
            timeout=settings.http_timeout_seconds,
        )
