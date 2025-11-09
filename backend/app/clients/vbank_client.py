"""HTTP client for VBank API."""
from app.core.base_client import BaseBankClient
from app.settings import settings


class VBankClient(BaseBankClient):
    """HTTP client for VBank API."""

    def __init__(self):
        """Initialize VBank client with settings."""
        super().__init__(
            base_url=settings.vbank_base_url,
            client_id=settings.vbank_client_id,
            client_secret=settings.vbank_client_secret,
            bank_code="vbank",
            timeout=settings.http_timeout_seconds,
        )
