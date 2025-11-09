"""Bank-related API endpoints."""
import logging
from datetime import datetime, timedelta
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
    LinkAccountRequest,
    LinkedAccountResponse,
    TestBalancesRequest,
)
from app.services.token_service import TokenService
from app.services.consent_service import ConsentService
from app.services.aggregation import AggregationService
from app.services.analytics import AnalyticsService
from app.services.cashback import CashbackService
from app.services.account_linking import AccountLinkingService
from app.core.exceptions import BankAPIError, ConsentRequiredError
from app.core.input_validation import (
    validate_bank_code,
    validate_client_id,
    validate_date_format,
    validate_period,
    validate_category,
    validate_bonus_percent,
)

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
        
        consent_status = consent_response.get("status", "")
        consent_id = consent_response.get("consent_id")
        request_id = consent_response.get("request_id")
        auto_approved = consent_response.get("auto_approved", False)
        
        # Prepare response message based on status
        message = None
        if consent_status == "pending" and request_id:
            # Manual approval required (SBank)
            bank_name = bank_lower.upper()
            message = (
                f"Согласие создано и ожидает одобрения. "
                f"Необходимо зайти в {bank_name} и одобрить запрос на доступ. "
                f"Request ID: {request_id}"
            )
        elif consent_status == "approved" and consent_id:
            # Auto-approved (VBank, ABank)
            message = "Согласие автоматически одобрено. Можно получать данные."
        
        return ConsentResponse(
            consent_id=consent_id,
            request_id=request_id,
            status=consent_status,
            auto_approved=auto_approved,
            bank=bank_lower,
            message=message,
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
    # Validate inputs
    client_id = validate_client_id(client_id)
    bank_codes = None
    if bank:
        bank_codes = [validate_bank_code(bank)]
    
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

    logger = logging.getLogger(__name__)
    try:
        transactions = await AggregationService.get_transactions(
            client_id, from_date=from_dt, to_date=to_dt, bank_codes=bank_codes
        )
        
        # If no real transactions but have linked accounts, show demo transactions
        # BUT: Only show demo if we don't have real account data
        # If we have real accounts, show empty transactions list (real data)
        linked_accounts = AccountLinkingService.get_linked_accounts(client_id)
        
        # Check if we have real account data
        try:
            real_accounts = await AggregationService.get_accounts(client_id)
            has_real_accounts = len(real_accounts) > 0
        except Exception:
            has_real_accounts = False
        
        if len(transactions) == 0 and len(linked_accounts) > 0 and not has_real_accounts:
            # Only show demo if we don't have real account data
            logger.info(f"Showing demo transactions: no real transactions and no real account data")
            # Check if we actually tried to get data (by checking if we have linked banks)
            linked_banks = AccountLinkingService.get_banks_for_client(client_id)
            # Only show demo if we have linked accounts but couldn't get real data
            # Generate demo transactions
            for i, acc in enumerate(linked_accounts[:3]):  # Max 3 accounts
                for j in range(5):  # 5 transactions per account
                    date = datetime.now() - timedelta(days=j*2)
                    demo_txn = type('Transaction', (), {
                        'transaction_id': f"demo-txn-{acc['bank']}-{i}-{j}",
                        'account_id': acc['account_number'],
                        'amount': str(-(1000 + j*500)),
                        'currency': 'RUB',
                        'booking_date': date.isoformat(),
                        'description': ['Покупка в магазине', 'Транспорт', 'Ресторан', 'Аптека', 'Развлечения'][j],
                        'mcc': ['5411', '4111', '5812', '5912', '7832'][j],
                    })()
                    transactions.append(demo_txn)
        elif len(transactions) == 0 and has_real_accounts:
            # Have real accounts but no transactions - show empty list (real data)
            logger.info(f"Real accounts exist but no transactions - showing empty transactions list")
            transactions = []
        
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

    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Getting analytics summary for client {client_id}, period {period_days} days")
        summary = await AnalyticsService.get_summary(client_id, period_days=period_days)
        logger.info(f"Analytics summary: net_worth={summary.get('net_worth', 0)}, total_accounts={summary.get('total_accounts', 0)}, total_spending={summary.get('total_spending', 0)}")
        return AnalyticsSummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}", exc_info=True)
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


@router.post("/accounts/link", response_model=LinkedAccountResponse)
async def link_account(
    request: LinkAccountRequest,
    client_id: str = Query(..., description="Client ID"),
) -> LinkedAccountResponse:
    """Link a bank account to a client.
    
    Args:
        request: Account linking request
        client_id: Client ID
        
    Returns:
        Linked account information
    """
    # Validate inputs
    client_id = validate_client_id(client_id)
    bank = validate_bank_code(request.bank)
    
    try:
        linked_account = AccountLinkingService.link_account(
            client_id=client_id,
            bank=bank,
            account_number=request.account_number,
            account_id=request.account_id,
            nickname=request.nickname,
        )
        
        return LinkedAccountResponse(
            id=linked_account["id"],
            bank=linked_account["bank"],
            account_number=linked_account["account_number"],
            account_id=linked_account.get("account_id"),
            nickname=linked_account["nickname"],
            linked_at=linked_account["linked_at"],
            active=linked_account["active"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link account: {str(e)}")


@router.get("/accounts/linked", response_model=list[LinkedAccountResponse])
async def get_linked_accounts(
    client_id: str = Query(..., description="Client ID"),
) -> list[LinkedAccountResponse]:
    """Get all linked accounts for a client.
    
    Args:
        client_id: Client ID
        
    Returns:
        List of linked accounts
    """
    # Validate input
    client_id = validate_client_id(client_id)
    
    try:
        accounts = AccountLinkingService.get_linked_accounts(client_id)
        return [
            LinkedAccountResponse(
                id=acc["id"],
                bank=acc["bank"],
                account_number=acc["account_number"],
                account_id=acc.get("account_id"),
                nickname=acc["nickname"],
                linked_at=acc["linked_at"],
                active=acc["active"],
            )
            for acc in accounts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get linked accounts: {str(e)}")


@router.delete("/accounts/link/{account_id}")
async def unlink_account(
    account_id: str,
    client_id: str = Query(..., description="Client ID"),
) -> dict[str, bool]:
    """Unlink a bank account.
    
    Args:
        account_id: Account ID to unlink
        client_id: Client ID
        
    Returns:
        Success status
    """
    # Validate input
    client_id = validate_client_id(client_id)
    
    try:
        success = AccountLinkingService.unlink_account(client_id, account_id)
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unlink account: {str(e)}")


@router.post("/test/balances", tags=["test"])
async def test_balances_manual(request: TestBalancesRequest) -> dict:
    """Test endpoint for manually testing balance retrieval with token.
    
    This endpoint allows you to:
    1. Get token from POST /api/tokens/{bank}
    2. Get consent_id from POST /api/consents/accounts
    3. Use this endpoint to test balance retrieval directly
    
    Args:
        request: Test request with bank, account_id, client_id, access_token, and optional consent_id
        
    Returns:
        Raw response from bank API
        
    Raises:
        HTTPException: If request fails
    """
    from app.clients.factory import get_bank_client
    from app.settings import settings
    
    # Validate bank code
    bank_lower = validate_bank_code(request.bank)
    client_id = validate_client_id(request.client_id)
    
    try:
        client = get_bank_client(bank_lower)
        try:
            # Make direct request to bank API
            balances_response = await client.get_balances(
                bank_token=request.access_token,
                account_id=request.account_id,
                client_id=client_id,
                requesting_bank=settings.requesting_bank_id,
                consent_id=request.consent_id,
            )
            return {
                "success": True,
                "bank": bank_lower,
                "account_id": request.account_id,
                "client_id": client_id,
                "consent_id": request.consent_id,
                "response": balances_response,
            }
        finally:
            await client.close()
    except BankAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Error testing balances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
