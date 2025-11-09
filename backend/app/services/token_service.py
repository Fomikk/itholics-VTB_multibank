"""Service for managing and caching bank tokens."""
from datetime import datetime, timedelta
from typing import Optional
from app.clients.factory import get_bank_client
from app.core.base_client import BaseBankClient
from app.settings import settings


class TokenCache:
    """Simple in-memory token cache."""

    def __init__(self):
        """Initialize token cache."""
        self._tokens: dict[str, dict] = {}

    def get(self, bank_code: str) -> Optional[dict]:
        """Get cached token if still valid.

        Args:
            bank_code: Bank code

        Returns:
            Token data if valid, None otherwise
        """
        if bank_code not in self._tokens:
            return None

        token_data = self._tokens[bank_code]
        expires_at = token_data.get("expires_at")

        if expires_at and datetime.now() >= expires_at:
            # Token expired
            del self._tokens[bank_code]
            return None

        return token_data

    def set(self, bank_code: str, token_data: dict) -> None:
        """Cache token data.

        Args:
            bank_code: Bank code
            token_data: Token response from bank
        """
        expires_in = token_data.get("expires_in", 86400)
        expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 1 min buffer

        self._tokens[bank_code] = {
            "access_token": token_data["access_token"],
            "token_type": token_data.get("token_type", "bearer"),
            "client_id": token_data.get("client_id"),
            "expires_in": expires_in,
            "expires_at": expires_at,
        }

    def clear(self, bank_code: Optional[str] = None) -> None:
        """Clear token cache.

        Args:
            bank_code: Bank code to clear, or None to clear all
        """
        if bank_code:
            self._tokens.pop(bank_code, None)
        else:
            self._tokens.clear()


# Global token cache instance
_token_cache = TokenCache()


class TokenService:
    """Service for managing bank tokens."""

    @staticmethod
    async def get_bank_token(bank_code: str, force_refresh: bool = False) -> dict:
        """Get bank token, using cache if available.

        Args:
            bank_code: Bank code (vbank, abank, sbank)
            force_refresh: Force token refresh even if cached

        Returns:
            Token data with access_token, expires_in, etc.
        """
        if not force_refresh:
            cached = _token_cache.get(bank_code)
            if cached:
                return cached

        # Get fresh token
        client = get_bank_client(bank_code)
        try:
            token_data = await client.get_bank_token()
            _token_cache.set(bank_code, token_data)
            return _token_cache.get(bank_code)
        finally:
            await client.close()

    @staticmethod
    def clear_cache(bank_code: Optional[str] = None) -> None:
        """Clear token cache.

        Args:
            bank_code: Bank code to clear, or None to clear all
        """
        _token_cache.clear(bank_code)

