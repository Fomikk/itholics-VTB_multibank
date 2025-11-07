"""Service for managing account consents."""
from typing import Optional
from app.clients.factory import get_bank_client
from app.services.token_service import TokenService
from app.settings import settings


class ConsentService:
    """Service for managing account consents."""

    @staticmethod
    async def request_accounts_consent(
        bank_code: str,
        client_id: str,
        permissions: Optional[list[str]] = None,
    ) -> dict:
        """Request account consent for interbank access.

        Args:
            bank_code: Bank code (vbank, abank, sbank)
            client_id: Client ID to request consent for
            permissions: List of permissions (default: ReadAccountsDetail, ReadBalances, ReadTransactions)

        Returns:
            Consent response with consent_id, status, etc.
        """
        if permissions is None:
            permissions = ["ReadAccountsDetail", "ReadBalances", "ReadTransactions"]

        # Get bank token
        token_data = await TokenService.get_bank_token(bank_code)
        bank_token = token_data["access_token"]

        # Request consent
        client = get_bank_client(bank_code)
        try:
            consent_response = await client.request_accounts_consent(
                bank_token=bank_token,
                client_id=client_id,
                permissions=permissions,
                requesting_bank=settings.requesting_bank_id,
                requesting_bank_name="FinGuru App",
                reason="Aggregation for FinGuru",
            )
            return consent_response
        finally:
            await client.close()

