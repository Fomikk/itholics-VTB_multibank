"""HTTP client for SBank API."""
from app.core.base_client import BaseBankClient
from app.settings import settings


class SBankClient(BaseBankClient):
    """HTTP client for SBank API."""

    def __init__(self):
        """Initialize SBank client with settings."""
        super().__init__(
            base_url=settings.sbank_base_url,
            client_id=settings.sbank_client_id,
            client_secret=settings.sbank_client_secret,
            bank_code="sbank",
            timeout=settings.http_timeout_seconds,
        )
