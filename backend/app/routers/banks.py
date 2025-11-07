"""Bank-related API endpoints."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.routers.schemas import (
    TokenResponse,
    ConsentRequest,
    ConsentResponse,
    AccountResponse,
    TransactionResponse,
    AnalyticsSummaryResponse,
    CashbackActivateRequest,
    CashbackActivateResponse,
)
from app.services.token_service import TokenService
from app.services.consent_service import ConsentService
from app.services.aggregation import AggregationService
from app.services.analytics import AnalyticsService
from app.services.cashback import CashbackService
from app.core.exceptions import BankAPIError, ConsentRequiredError

router = APIRouter(prefix="/api", tags=["banks"])


@router.post("/tokens/{bank}", response_model=TokenResponse)
async def get_bank_token(bank: str, force_refresh: bool = False) -> TokenResponse:
    """Get and cache bank token.

    Args:
        bank: Bank code (vbank, abank, sbank)
        force_refresh: Force token refresh even if cached

    Returns:
        Token response with access_token, expires_in, etc.

    Raises:
        HTTPException: If bank code is invalid or request fails
    """
    # Validate bank code
    bank_lower = validate_bank_code(bank)

    try:
        token_data = await TokenService.get_bank_token(bank_lower, force_refresh=force_refresh)
        return TokenResponse(
            access_token=token_data["access_token"],
            expires_in=token_data["expires_in"],
            bank=bank_lower,
            token_type=token_data.get("token_type", "bearer"),
        )
    except BankAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/consents/accounts", response_model=ConsentResponse)
async def create_account_consent(request: ConsentRequest) -> ConsentResponse:
    """Create account consent for interbank access.

    Args:
        request: Consent request with bank, client_id, and permissions

    Returns:
        Consent response with consent_id, status, etc.

    Raises:
        HTTPException: If bank code is invalid or request fails
    """
    # Validate bank code and client ID
    bank_lower = validate_bank_code(request.bank)
    client_id = validate_client_id(request.client_id)

    try:
        consent_response = await ConsentService.request_accounts_consent(
            bank_code=bank_lower,
            client_id=client_id,
            permissions=request.permissions,
        )

        return ConsentResponse(
            consent_id=consent_response["consent_id"],
            status=consent_response["status"],
            auto_approved=consent_response.get("auto_approved", False),
            bank=bank_lower,
        )
    except BankAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/accounts/aggregate", response_model=list[AccountResponse])
async def aggregate_accounts(
    client_id: str = Query(..., description="Client ID"),
    bank: Optional[str] = Query(None, description="Filter by specific bank (vbank, abank, sbank)"),
) -> list[AccountResponse]:
    """Aggregate accounts from all banks.

    Args:
        client_id: Client ID
        bank: Optional bank code to filter by

    Returns:
        List of unified accounts

    Raises:
        HTTPException: If aggregation fails
    """
    # Validate inputs
    client_id = validate_client_id(client_id)
    bank_codes = None
    if bank:
        bank_codes = [validate_bank_code(bank)]

    try:
        accounts = await AggregationService.get_accounts(client_id, bank_codes=bank_codes)
        return [
            AccountResponse(
                account_id=acc.account_id,
                bank=acc.bank,
                currency=acc.currency,
                account_type=acc.account_type,
                nickname=acc.nickname,
                servicer=acc.servicer,
            )
            for acc in accounts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to aggregate accounts: {str(e)}")


@router.get("/transactions/aggregate", response_model=list[TransactionResponse])
async def aggregate_transactions(
    client_id: str = Query(..., description="Client ID"),
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format, e.g., 2024-01-01T00:00:00)"
    ),
    to_date: Optional[str] = Query(
        None, description="End date (ISO format, e.g., 2024-01-31T23:59:59)"
    ),
    bank: Optional[str] = Query(None, description="Filter by specific bank (vbank, abank, sbank)"),
) -> list[TransactionResponse]:
    """Aggregate transactions from all accounts.

    Args:
        client_id: Client ID
        from_date: Start date (ISO format)
        to_date: End date (ISO format)
        bank: Optional bank code to filter by

    Returns:
        List of unified transactions

    Raises:
        HTTPException: If aggregation fails
    """
    bank_codes = None
    if bank:
        bank_lower = bank.lower()
        if bank_lower not in ["vbank", "abank", "sbank"]:
            raise HTTPException(
                status_code=400, detail=f"Invalid bank code: {bank_lower}. Must be vbank, abank, or sbank"
            )
        bank_codes = [bank_lower]

    # Validate inputs
    client_id = validate_client_id(client_id)
    
    # Parse and validate dates
    from_dt = None
    to_dt = None
    if from_date:
        from_dt = validate_date_format(from_date)
    if to_date:
        to_dt = validate_date_format(to_date)
    
    # Validate date range
    if from_dt and to_dt and from_dt > to_dt:
        raise HTTPException(status_code=400, detail="from_date must be before to_date")

    try:
        transactions = await AggregationService.get_transactions(
            client_id, from_date=from_dt, to_date=to_dt, bank_codes=bank_codes
        )
        return [
            TransactionResponse(
                transaction_id=txn.transaction_id,
                account_id=txn.account_id,
                amount=txn.amount,
                currency=txn.currency,
                booking_date=txn.booking_date,
                description=txn.description,
                mcc=txn.mcc,
            )
            for txn in transactions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to aggregate transactions: {str(e)}")


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    client_id: str = Query(..., description="Client ID"),
    period: str = Query("30d", description="Period (e.g., 30d, 7d, 90d)"),
) -> AnalyticsSummaryResponse:
    """Get financial analytics summary for dashboard.

    Args:
        client_id: Client ID
        period: Period string (e.g., "30d" for 30 days)

    Returns:
        Analytics summary with net worth, spending by category, etc.

    Raises:
        HTTPException: If analytics calculation fails
    """
    # Validate inputs
    client_id = validate_client_id(client_id)
    period_days = validate_period(period)

    try:
        summary = await AnalyticsService.get_summary(client_id, period_days=period_days)
        return AnalyticsSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")


@router.post("/cashback/activate", response_model=CashbackActivateResponse)
async def activate_cashback(request: CashbackActivateRequest) -> CashbackActivateResponse:
    """Activate cashback bonus for a category.

    Args:
        request: Cashback activation request

    Returns:
        Cashback activation response

    Raises:
        HTTPException: If activation fails
    """
    # Validate inputs
    client_id = validate_client_id(request.client_id)
    category = validate_category(request.category)
    bonus_percent = validate_bonus_percent(request.bonus_percent)
    
    try:
        bonus = CashbackService.activate_cashback(
            client_id=client_id,
            category=category,
            bonus_percent=bonus_percent,
            valid_until=request.valid_until,
        )

        return CashbackActivateResponse(
            activated=True,
            category=bonus.category,
            bonus_percent=bonus.bonus_percent,
            valid_until=bonus.valid_until,
            activated_at=bonus.activated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate cashback: {str(e)}")


@router.get("/cashback/active")
async def get_active_cashback(
    client_id: str = Query(..., description="Client ID"),
) -> list[dict]:
    """Get active cashback bonuses for a client.

    Args:
        client_id: Client ID

    Returns:
        List of active cashback bonuses
    """
    # Validate input
    client_id = validate_client_id(client_id)
    try:
        bonuses = CashbackService.get_active_bonuses(client_id)
        return [
            {
                "category": bonus.category,
                "bonus_percent": bonus.bonus_percent,
                "valid_until": bonus.valid_until.isoformat(),
                "activated_at": bonus.activated_at.isoformat(),
            }
            for bonus in bonuses
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active cashback: {str(e)}")
