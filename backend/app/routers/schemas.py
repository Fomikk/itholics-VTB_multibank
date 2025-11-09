"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# Token schemas
class TokenResponse(BaseModel):
    """Response for token endpoint."""

    access_token: str
    expires_in: int
    bank: str
    token_type: str = "bearer"


# Consent schemas
class ConsentRequest(BaseModel):
    """Request for creating account consent."""

    bank: str = Field(..., description="Bank code (vbank, abank, sbank)")
    client_id: str = Field(..., description="Client ID")
    permissions: Optional[list[str]] = Field(
        default=None,
        description="List of permissions (default: ReadAccountsDetail, ReadBalances, ReadTransactions)",
    )


class ConsentResponse(BaseModel):
    """Response for consent creation."""

    consent_id: Optional[str] = None
    request_id: Optional[str] = None
    status: str
    auto_approved: bool
    bank: str
    message: Optional[str] = None


# Account schemas
class AccountResponse(BaseModel):
    """Unified account response."""

    account_id: str
    bank: str
    currency: str
    account_type: str
    nickname: Optional[str] = None
    servicer: Optional[dict[str, Any]] = None


# Transaction schemas
class TransactionResponse(BaseModel):
    """Unified transaction response."""

    transaction_id: str
    account_id: str
    amount: str
    currency: str
    booking_date: str
    description: Optional[str] = None
    mcc: Optional[str] = None


# Analytics schemas
class AnalyticsSummaryResponse(BaseModel):
    """Analytics summary response."""

    net_worth: float
    total_accounts: int
    total_spending: float
    spending_by_category: dict[str, float]
    top_expenses: list[dict[str, Any]]
    weekly_trend: list[dict[str, Any]]
    period_days: int


# Cashback schemas
class CashbackActivateRequest(BaseModel):
    """Request for activating cashback."""

    client_id: str
    category: str = Field(..., description="Spending category (e.g., groceries, restaurants)")
    bonus_percent: float = Field(..., ge=0, le=100, description="Bonus percentage (0-100)")
    valid_until: Optional[datetime] = Field(
        default=None, description="Expiration date (default: 30 days from now)"
    )


class CashbackActivateResponse(BaseModel):
    """Response for cashback activation."""

    activated: bool
    category: str
    bonus_percent: float
    valid_until: datetime
    activated_at: datetime


# Account linking schemas
class LinkAccountRequest(BaseModel):
    """Request for linking a bank account."""

    bank: str = Field(..., description="Bank code (vbank, abank, sbank)")
    account_number: str = Field(..., description="Account number or identifier")
    account_id: Optional[str] = Field(None, description="Account ID from bank API (optional)")
    nickname: Optional[str] = Field(None, description="Nickname for the account")


class LinkedAccountResponse(BaseModel):
    """Response for linked account."""

    id: str
    bank: str
    account_number: str
    account_id: Optional[str] = None
    nickname: str
    linked_at: str
    active: bool


# Test schemas for manual testing
class TestBalancesRequest(BaseModel):
    """Request for testing balances with manual token."""

    bank: str = Field(..., description="Bank code (vbank, abank, sbank)")
    account_id: str = Field(..., description="Account ID")
    client_id: str = Field(..., description="Client ID (e.g., team268-1)")
    access_token: str = Field(..., description="Access token from POST /api/tokens/{bank}")
    consent_id: Optional[str] = Field(None, description="Consent ID (optional, will be used if provided)")
