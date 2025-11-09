"""Common types for bank clients."""
from typing import Any, Optional
from pydantic import BaseModel


class BankTokenResponse(BaseModel):
    """Response from bank token endpoint."""

    access_token: str
    token_type: str = "bearer"
    client_id: str
    expires_in: int


class ConsentRequest(BaseModel):
    """Request for account consent."""

    client_id: str
    permissions: list[str]
    reason: str
    requesting_bank: str
    requesting_bank_name: str


class ConsentResponse(BaseModel):
    """Response from consent request."""

    status: str
    consent_id: str
    auto_approved: bool


class Account(BaseModel):
    """Unified account model."""

    account_id: str
    bank: str
    currency: str
    account_type: str
    nickname: Optional[str] = None
    servicer: Optional[dict[str, Any]] = None


class Balance(BaseModel):
    """Unified balance model."""

    account_id: str
    amount: str
    currency: str
    balance_type: str


class Transaction(BaseModel):
    """Unified transaction model."""

    transaction_id: str
    account_id: str
    amount: str
    currency: str
    booking_date: str
    description: Optional[str] = None
    mcc: Optional[str] = None

