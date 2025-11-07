"""Base HTTP client for bank APIs."""
from typing import Any, Optional
import httpx
from app.core.exceptions import BankAPIError


class BaseBankClient:
    """Base class for bank HTTP clients."""

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        bank_code: str,
        timeout: int = 15,
    ):
        """Initialize bank client.

        Args:
            base_url: Base URL of the bank API
            client_id: Client ID for authentication
            client_secret: Client secret for authentication
            bank_code: Bank code (vbank, abank, sbank)
            timeout: HTTP request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.bank_code = bank_code
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

    def _build_headers(
        self,
        token: str,
        requesting_bank: Optional[str] = None,
        consent_id: Optional[str] = None,
    ) -> dict[str, str]:
        """Build request headers.

        Args:
            token: Bearer token
            requesting_bank: Requesting bank ID for interbank requests
            consent_id: Consent ID for interbank requests

        Returns:
            Dictionary of headers
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        if requesting_bank:
            headers["X-Requesting-Bank"] = requesting_bank

        if consent_id:
            headers["X-Consent-Id"] = consent_id

        return headers

    async def get_bank_token(self) -> dict:
        """Get bank token for API access.

        Returns:
            Token response with access_token, expires_in, etc.

        Raises:
            BankAPIError: If request fails
        """
        url = f"{self.base_url}/auth/bank-token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = await self._client.post(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BankAPIError(
                status_code=e.response.status_code,
                detail=f"Failed to get bank token: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise BankAPIError(
                status_code=503,
                detail=f"Network error while getting bank token: {str(e)}",
            )

    async def request_accounts_consent(
        self,
        bank_token: str,
        client_id: str,
        permissions: list[str],
        requesting_bank: str,
        requesting_bank_name: str = "FinGuru App",
        reason: str = "Aggregation for FinGuru",
    ) -> dict:
        """Request account consent for interbank access.

        Args:
            bank_token: Bank token for authentication
            client_id: Client ID to request consent for
            permissions: List of permissions (e.g., ["ReadAccountsDetail", "ReadBalances"])
            requesting_bank: Requesting bank ID
            requesting_bank_name: Name of requesting bank
            reason: Reason for consent request

        Returns:
            Consent response with consent_id, status, etc.

        Raises:
            BankAPIError: If request fails
        """
        url = f"{self.base_url}/account-consents/request"
        headers = self._build_headers(bank_token, requesting_bank=requesting_bank)
        payload = {
            "client_id": client_id,
            "permissions": permissions,
            "reason": reason,
            "requesting_bank": requesting_bank,
            "requesting_bank_name": requesting_bank_name,
        }

        try:
            response = await self._client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BankAPIError(
                status_code=e.response.status_code,
                detail=f"Failed to request consent: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise BankAPIError(
                status_code=503,
                detail=f"Network error while requesting consent: {str(e)}",
            )

    async def get_accounts(
        self,
        bank_token: str,
        client_id: Optional[str] = None,
        requesting_bank: Optional[str] = None,
        consent_id: Optional[str] = None,
    ) -> dict:
        """Get list of accounts.

        Args:
            bank_token: Bank token for authentication
            client_id: Client ID (required for interbank requests)
            requesting_bank: Requesting bank ID (for interbank requests)
            consent_id: Consent ID (for interbank requests)

        Returns:
            Accounts response

        Raises:
            BankAPIError: If request fails
        """
        url = f"{self.base_url}/accounts"
        headers = self._build_headers(
            bank_token, requesting_bank=requesting_bank, consent_id=consent_id
        )
        params = {}
        if client_id:
            params["client_id"] = client_id

        try:
            response = await self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                error_detail = e.response.text
                if "CONSENT_REQUIRED" in error_detail or "consent" in error_detail.lower():
                    from app.core.exceptions import ConsentRequiredError

                    raise ConsentRequiredError(
                        status_code=403,
                        detail="Consent is required for this operation",
                    )
            raise BankAPIError(
                status_code=e.response.status_code,
                detail=f"Failed to get accounts: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise BankAPIError(
                status_code=503,
                detail=f"Network error while getting accounts: {str(e)}",
            )

    async def get_account_details(
        self,
        bank_token: str,
        account_id: str,
        client_id: Optional[str] = None,
        requesting_bank: Optional[str] = None,
        consent_id: Optional[str] = None,
    ) -> dict:
        """Get account details.

        Args:
            bank_token: Bank token for authentication
            account_id: Account ID
            client_id: Client ID (for interbank requests)
            requesting_bank: Requesting bank ID (for interbank requests)
            consent_id: Consent ID (for interbank requests)

        Returns:
            Account details response

        Raises:
            BankAPIError: If request fails
        """
        url = f"{self.base_url}/accounts/{account_id}"
        headers = self._build_headers(
            bank_token, requesting_bank=requesting_bank, consent_id=consent_id
        )
        params = {}
        if client_id:
            params["client_id"] = client_id

        try:
            response = await self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BankAPIError(
                status_code=e.response.status_code,
                detail=f"Failed to get account details: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise BankAPIError(
                status_code=503,
                detail=f"Network error while getting account details: {str(e)}",
            )

    async def get_balances(
        self,
        bank_token: str,
        account_id: str,
        client_id: Optional[str] = None,
        requesting_bank: Optional[str] = None,
        consent_id: Optional[str] = None,
    ) -> dict:
        """Get account balances.

        Args:
            bank_token: Bank token for authentication
            account_id: Account ID
            client_id: Client ID (for interbank requests)
            requesting_bank: Requesting bank ID (for interbank requests)
            consent_id: Consent ID (for interbank requests)

        Returns:
            Balances response

        Raises:
            BankAPIError: If request fails
        """
        url = f"{self.base_url}/accounts/{account_id}/balances"
        headers = self._build_headers(
            bank_token, requesting_bank=requesting_bank, consent_id=consent_id
        )
        params = {}
        if client_id:
            params["client_id"] = client_id

        try:
            response = await self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BankAPIError(
                status_code=e.response.status_code,
                detail=f"Failed to get balances: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise BankAPIError(
                status_code=503,
                detail=f"Network error while getting balances: {str(e)}",
            )

    async def get_transactions(
        self,
        bank_token: str,
        account_id: str,
        client_id: Optional[str] = None,
        requesting_bank: Optional[str] = None,
        consent_id: Optional[str] = None,
        from_booking_date_time: Optional[str] = None,
        to_booking_date_time: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict:
        """Get account transactions.

        Args:
            bank_token: Bank token for authentication
            account_id: Account ID
            client_id: Client ID (for interbank requests)
            requesting_bank: Requesting bank ID (for interbank requests)
            consent_id: Consent ID (for interbank requests)
            from_booking_date_time: Start date (ISO format)
            to_booking_date_time: End date (ISO format)
            page: Page number
            limit: Number of transactions per page (max 500)

        Returns:
            Transactions response

        Raises:
            BankAPIError: If request fails
        """
        url = f"{self.base_url}/accounts/{account_id}/transactions"
        headers = self._build_headers(
            bank_token, requesting_bank=requesting_bank, consent_id=consent_id
        )
        params: dict[str, Any] = {
            "page": page,
            "limit": min(limit, 500),  # Cap at 500
        }
        if client_id:
            params["client_id"] = client_id
        if from_booking_date_time:
            params["from_booking_date_time"] = from_booking_date_time
        if to_booking_date_time:
            params["to_booking_date_time"] = to_booking_date_time

        try:
            response = await self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BankAPIError(
                status_code=e.response.status_code,
                detail=f"Failed to get transactions: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise BankAPIError(
                status_code=503,
                detail=f"Network error while getting transactions: {str(e)}",
            )

