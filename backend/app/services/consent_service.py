"""Service for managing account consents."""
from typing import Optional
from app.clients.factory import get_bank_client
from app.services.token_service import TokenService
from app.settings import settings


class ConsentService:
    """Service for managing account consents."""
    
    # In-memory storage for consent IDs (client_id, bank_code) -> consent_id
    _consent_ids: dict[tuple[str, str], str] = {}

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
            Consent response with consent_id (if auto-approved) or request_id (if pending)
            - VBank/ABank: returns consent_id immediately with status="approved"
            - SBank: returns request_id with status="pending" (requires manual approval)
        """
        if permissions is None:
            # Default permissions for account aggregation
            # These permissions are required to read accounts, balances, and transactions
            permissions = ["ReadAccountsDetail", "ReadBalances", "ReadTransactions"]

        # Step 1: Get bank token for interbank requests
        # POST /auth/bank-token?client_id=team268&client_secret=...
        token_data = await TokenService.get_bank_token(bank_code)
        bank_token = token_data["access_token"]

        # Step 2: Request consent for interbank access
        # POST /account-consents/request
        # Headers: Authorization: Bearer <bank_token>, X-Requesting-Bank: team268
        # Body: { permissions: [...], client_id: "team268-1", requesting_bank: "team268" }
        # Note: X-Requesting-Bank must be "team268" (team ID without suffix), not "team268-1"
        client = get_bank_client(bank_code)
        try:
            consent_response = await client.request_accounts_consent(
                bank_token=bank_token,
                client_id=client_id,  # e.g., "team268-1" (client ID with suffix)
                permissions=permissions,
                requesting_bank=settings.requesting_bank_id,  # "team268" (team ID without suffix)
                requesting_bank_name="FinGuru App",
                reason="Aggregation for FinGuru",
            )
            
            # Add bank code to response for consistency
            consent_response["bank"] = bank_code
            
            # Store consent_id if approved
            consent_id = consent_response.get("consent_id")
            if consent_id and consent_response.get("status") == "approved":
                ConsentService._consent_ids[(client_id, bank_code)] = consent_id
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"💾 Stored consent_id={consent_id} for client_id={client_id}, bank_code={bank_code}")
            
            return consent_response
        finally:
            await client.close()
    
    @staticmethod
    def get_consent_id(client_id: str, bank_code: str) -> Optional[str]:
        """Get stored consent ID for a client and bank.
        
        Args:
            client_id: Client ID
            bank_code: Bank code
            
        Returns:
            Consent ID if available, None otherwise
        """
        return ConsentService._consent_ids.get((client_id, bank_code))
    
    @staticmethod
    def clear_consent_id(client_id: str, bank_code: str) -> None:
        """Clear stored consent ID for a client and bank.
        
        Args:
            client_id: Client ID
            bank_code: Bank code
        """
        ConsentService._consent_ids.pop((client_id, bank_code), None)

