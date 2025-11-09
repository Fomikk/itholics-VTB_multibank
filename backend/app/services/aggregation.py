"""Service for aggregating data from multiple banks."""
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional
from app.clients.factory import get_all_bank_clients, get_bank_client
from app.core.exceptions import ConsentRequiredError
from app.core.types import Account, Balance, Transaction
from app.services.consent_service import ConsentService
from app.services.token_service import TokenService
from app.services.account_linking import AccountLinkingService
from app.settings import settings


def _has_bank_credentials(bank_code: str) -> bool:
    """Check if bank has credentials configured.
    
    Args:
        bank_code: Bank code (vbank, abank, sbank)
        
    Returns:
        True if credentials are configured, False otherwise
    """
    bank_code_lower = bank_code.lower()
    if bank_code_lower == "vbank":
        return bool(settings.vbank_client_id and settings.vbank_client_secret)
    elif bank_code_lower == "abank":
        return bool(settings.abank_client_id and settings.abank_client_secret)
    elif bank_code_lower == "sbank":
        return bool(settings.sbank_client_id and settings.sbank_client_secret)
    return False


class AggregationService:
    """Service for aggregating financial data from multiple banks."""

    @staticmethod
    def _normalize_account(account_data: dict, bank_code: str) -> Account:
        """Normalize account data to unified format.

        Args:
            account_data: Raw account data from bank API
            bank_code: Bank code

        Returns:
            Normalized Account object
        """
        # API returns accountId (camelCase), normalize to account_id (snake_case)
        account_id = account_data.get("accountId") or account_data.get("account_id", "")
        # API returns accountType (camelCase), normalize to account_type (snake_case)
        account_type = account_data.get("accountType") or account_data.get("account_type", "Personal")
        
        return Account(
            account_id=account_id,
            bank=bank_code,
            currency=account_data.get("currency", "RUB"),
            account_type=account_type,
            nickname=account_data.get("nickname"),
            servicer=account_data.get("servicer"),
        )

    @staticmethod
    def _normalize_balance(balance_data: dict, account_id: str) -> Balance:
        """Normalize balance data to unified format.

        Args:
            balance_data: Raw balance data from bank API
            account_id: Account ID

        Returns:
            Normalized Balance object
        """
        # API may return balanceType (camelCase) or balance_type (snake_case)
        balance_type = balance_data.get("balanceType") or balance_data.get("balance_type", "interimBooked")
        
        # Handle amount - may be a string, number, or dict with amount/currency
        amount_value = balance_data.get("amount", "0")
        if isinstance(amount_value, dict):
            # If amount is a dict like {"amount": "0.00", "currency": "RUB"}
            amount_str = str(amount_value.get("amount", "0"))
            currency = amount_value.get("currency") or balance_data.get("currency", "RUB")
        else:
            amount_str = str(amount_value)
            currency = balance_data.get("currency", "RUB")
        
        return Balance(
            account_id=account_id,
            amount=amount_str,
            currency=currency,
            balance_type=balance_type,
        )

    @staticmethod
    def _normalize_transaction(transaction_data: dict, account_id: str) -> Transaction:
        """Normalize transaction data to unified format.

        Args:
            transaction_data: Raw transaction data from bank API
            account_id: Account ID

        Returns:
            Normalized Transaction object
        """
        # API may return camelCase or snake_case fields
        transaction_id = transaction_data.get("transactionId") or transaction_data.get("transaction_id", "")
        booking_date = transaction_data.get("bookingDateTime") or transaction_data.get("booking_date_time", transaction_data.get("booking_date", ""))
        
        return Transaction(
            transaction_id=transaction_id,
            account_id=account_id,
            amount=str(transaction_data.get("amount", "0")),
            currency=transaction_data.get("currency", "RUB"),
            booking_date=booking_date,
            description=transaction_data.get("description"),
            mcc=transaction_data.get("mcc"),
        )

    @staticmethod
    async def get_accounts(
        client_id: str, bank_codes: Optional[list[str]] = None
    ) -> list[Account]:
        """Aggregate accounts from all banks.

        Args:
            client_id: Client ID
            bank_codes: List of bank codes to query (None = all banks or linked banks)

        Returns:
            List of normalized accounts
        """
        # If no bank codes specified, use linked accounts or all banks
        if bank_codes is None:
            linked_banks = AccountLinkingService.get_banks_for_client(client_id)
            bank_codes = linked_banks if linked_banks else ["vbank", "abank", "sbank"]

        all_accounts: list[Account] = []
        
        import logging
        logger = logging.getLogger(__name__)

        for bank_code in bank_codes:
            # Check if credentials are available
            if not _has_bank_credentials(bank_code):
                # Skip this bank if no credentials - will use demo data later
                logger.info(f"Skipping {bank_code}: no credentials configured")
                continue
            
            logger.info(f"Attempting to get accounts from {bank_code} for client {client_id}")
                
            try:
                # Step 1: Get bank token for interbank requests
                # POST /auth/bank-token?client_id=team268&client_secret=...
                token_data = await TokenService.get_bank_token(bank_code)
                bank_token = token_data["access_token"]

                client = get_bank_client(bank_code)
                try:
                    # Step 3: Get accounts (interbank request)
                    # GET /accounts?client_id=team268-1
                    # Headers: Authorization: Bearer <bank_token>, X-Requesting-Bank: team268
                    # Note: X-Consent-Id will be added if consent is required and created
                    accounts_response = await asyncio.wait_for(
                        client.get_accounts(
                            bank_token=bank_token,
                            client_id=client_id,
                            requesting_bank=settings.requesting_bank_id,  # team268 (without suffix)
                        ),
                        timeout=5.0  # 5 second timeout for getting accounts
                    )

                    # API returns accounts in data.account (not data.accounts)
                    # Handle both formats: {"data": {"account": [...]}} and {"accounts": [...]}
                    accounts_list = []
                    
                    # Debug: log the response structure
                    logger.info(f"🔍 Parsing accounts response from {bank_code} (before consent): keys={list(accounts_response.keys())}")
                    
                    # Try data.account first (most common format)
                    data_section = accounts_response.get("data")
                    if data_section:
                        logger.info(f"🔍 Found 'data' section: type={type(data_section)}, keys={list(data_section.keys()) if isinstance(data_section, dict) else 'N/A'}")
                        if isinstance(data_section, dict):
                            # Try data.account (single account or list)
                            account_data = data_section.get("account")
                            if account_data:
                                logger.info(f"🔍 Found 'account' in data: type={type(account_data)}, length={len(account_data) if isinstance(account_data, list) else 1 if isinstance(account_data, dict) else 'N/A'}")
                                if isinstance(account_data, list):
                                    accounts_list = account_data
                                    logger.info(f"✅ Extracted {len(accounts_list)} accounts from list")
                                elif isinstance(account_data, dict):
                                    accounts_list = [account_data]
                                    logger.info(f"✅ Wrapped single account dict into list")
                                else:
                                    logger.warning(f"⚠️ Unexpected account data type: {type(account_data)}, value={account_data}")
                            else:
                                logger.warning(f"⚠️ 'account' key not found in data section. Available keys: {list(data_section.keys())}")
                        else:
                            logger.warning(f"⚠️ 'data' section is not a dict: {type(data_section)}")
                    else:
                        logger.warning(f"⚠️ 'data' key not found in response. Available keys: {list(accounts_response.keys())}")
                    
                    # Fallback to top-level accounts
                    if not accounts_list:
                        accounts_list = accounts_response.get("accounts", [])
                        if accounts_list:
                            logger.info(f"🔍 Found 'accounts' at top level: {len(accounts_list)} items")
                    
                    # Ensure accounts_list is a list
                    if not isinstance(accounts_list, list):
                        logger.warning(f"accounts_list is not a list: {type(accounts_list)}, value={accounts_list}")
                        accounts_list = []
                    
                    logger.info(f"Got {len(accounts_list)} accounts from {bank_code} (before consent)")
                    if len(accounts_list) == 0:
                        logger.warning(f"⚠️ No accounts parsed from {bank_code} response (before consent). Full response: {accounts_response}")
                        # Check if we have linked accounts for this bank
                        linked_accounts_for_bank = [acc for acc in AccountLinkingService.get_linked_accounts(client_id) if acc['bank'] == bank_code]
                        if linked_accounts_for_bank:
                            logger.info(f"Found {len(linked_accounts_for_bank)} linked accounts for {bank_code}, will use them for balances/transactions")
                    else:
                        logger.info(f"✅ Successfully parsed {len(accounts_list)} accounts from {bank_code} (before consent)")
                        for account_data in accounts_list:
                            normalized = AggregationService._normalize_account(
                                account_data, bank_code
                            )
                            all_accounts.append(normalized)
                            logger.info(f"✅ Account from {bank_code}: account_id={normalized.account_id}, type={normalized.account_type}, currency={normalized.currency}, nickname={normalized.nickname}")

                except ConsentRequiredError:
                    # Step 2: Create consent for interbank access
                    # POST /account-consents/request
                    # Headers: Authorization: Bearer <bank_token>, X-Requesting-Bank: team268
                    # Body: { permissions: [...], client_id: "team268-1", requesting_bank: "team268" }
                    try:
                        # Add timeout for consent creation
                        consent_response = await asyncio.wait_for(
                            ConsentService.request_accounts_consent(
                                bank_code=bank_code,
                                client_id=client_id,
                                permissions=["ReadAccountsDetail", "ReadBalances", "ReadTransactions"],
                            ),
                            timeout=5.0  # 5 second timeout for consent creation
                        )
                        
                        consent_status = consent_response.get("status", "")
                        consent_id = consent_response.get("consent_id")
                        request_id = consent_response.get("request_id")
                        auto_approved = consent_response.get("auto_approved", False)
                        
                        # Check if consent was automatically approved (VBank, ABank)
                        if consent_status == "approved" and consent_id and auto_approved:
                            logger.info(f"✅ Consent approved for {bank_code}, consent_id={consent_id}, retrying accounts request")
                            # Retry Step 3 with consent_id
                            # GET /accounts?client_id=team268-1
                            # Headers: Authorization: Bearer <bank_token>, X-Requesting-Bank: team268, X-Consent-Id: <consent_id>
                            accounts_response = await asyncio.wait_for(
                                client.get_accounts(
                                    bank_token=bank_token,
                                    client_id=client_id,
                                    requesting_bank=settings.requesting_bank_id,  # team268 (without suffix)
                                    consent_id=consent_id,  # Required for interbank requests
                                ),
                                timeout=5.0  # 5 second timeout for getting accounts
                            )

                            # API returns accounts in data.account (not data.accounts)
                            # Handle both formats: {"data": {"account": [...]}} and {"accounts": [...]}
                            accounts_list = []
                            
                            # Debug: log the response structure
                            logger.info(f"🔍 Parsing accounts response from {bank_code}: keys={list(accounts_response.keys())}")
                            
                            # Try data.account first (most common format)
                            data_section = accounts_response.get("data")
                            if data_section:
                                logger.info(f"🔍 Found 'data' section: type={type(data_section)}, keys={list(data_section.keys()) if isinstance(data_section, dict) else 'N/A'}")
                                if isinstance(data_section, dict):
                                    # Try data.account (single account or list)
                                    account_data = data_section.get("account")
                                    if account_data:
                                        logger.info(f"🔍 Found 'account' in data: type={type(account_data)}, length={len(account_data) if isinstance(account_data, list) else 1 if isinstance(account_data, dict) else 'N/A'}")
                                        if isinstance(account_data, list):
                                            accounts_list = account_data
                                            logger.info(f"✅ Extracted {len(accounts_list)} accounts from list")
                                        elif isinstance(account_data, dict):
                                            accounts_list = [account_data]
                                            logger.info(f"✅ Wrapped single account dict into list")
                                        else:
                                            logger.warning(f"⚠️ Unexpected account data type: {type(account_data)}, value={account_data}")
                                    else:
                                        logger.warning(f"⚠️ 'account' key not found in data section. Available keys: {list(data_section.keys())}")
                                else:
                                    logger.warning(f"⚠️ 'data' section is not a dict: {type(data_section)}")
                            else:
                                logger.warning(f"⚠️ 'data' key not found in response. Available keys: {list(accounts_response.keys())}")
                            
                            # Fallback to top-level accounts
                            if not accounts_list:
                                accounts_list = accounts_response.get("accounts", [])
                                if accounts_list:
                                    logger.debug(f"Found 'accounts' at top level: {len(accounts_list)} items")
                            
                            # Ensure accounts_list is a list
                            if not isinstance(accounts_list, list):
                                logger.warning(f"accounts_list is not a list: {type(accounts_list)}, value={accounts_list}")
                                accounts_list = []
                            
                            logger.info(f"Got {len(accounts_list)} accounts from {bank_code} (after consent, consent_id={consent_id})")
                            if len(accounts_list) == 0:
                                logger.warning(f"⚠️ No accounts parsed from {bank_code} response. Full response: {accounts_response}")
                            else:
                                logger.info(f"✅ Successfully parsed {len(accounts_list)} accounts from {bank_code}")
                            if len(accounts_list) > 0:
                                for account_data in accounts_list:
                                    normalized = AggregationService._normalize_account(
                                        account_data, bank_code
                                    )
                                    all_accounts.append(normalized)
                                    logger.info(f"✅ Account from {bank_code}: account_id={normalized.account_id}, type={normalized.account_type}, currency={normalized.currency}, nickname={normalized.nickname}")
                            else:
                                logger.warning(f"API returned 0 accounts from {bank_code} for client {client_id} even after consent approval. Full response: {accounts_response}")
                                # Check if we have linked accounts for this bank that we can use
                                linked_accounts_for_bank = [acc for acc in AccountLinkingService.get_linked_accounts(client_id) if acc['bank'] == bank_code]
                                if linked_accounts_for_bank:
                                    logger.info(f"Will use {len(linked_accounts_for_bank)} linked accounts for {bank_code} to get balances/transactions directly")
                                    for linked_acc in linked_accounts_for_bank:
                                        logger.info(f"Linked account: bank={linked_acc['bank']}, account_number={linked_acc['account_number']}, account_id={linked_acc.get('account_id', 'N/A')}")
                        elif consent_status == "pending" and request_id:
                            # Consent requires manual approval (SBank)
                            # Skip this bank for now - user needs to approve consent in bank
                            # Will use demo data instead
                            pass
                    except asyncio.TimeoutError:
                        # Skip this bank if consent creation or account retrieval times out
                        logger.warning(f"Timeout creating consent or getting accounts from {bank_code} for client {client_id}")
                        pass
                    except Exception as e:
                        # Skip this bank if consent creation fails
                        logger.error(f"Error creating consent or getting accounts from {bank_code} for client {client_id}: {e}")
                        pass
                except asyncio.TimeoutError:
                    # Skip this bank if request times out
                    logger.warning(f"Timeout getting accounts from {bank_code} for client {client_id}")
                    pass
                except Exception as e:
                    # Skip this bank if request fails
                    logger.error(f"Error getting accounts from {bank_code} for client {client_id}: {e}")
                    pass
                finally:
                    await client.close()

            except Exception:
                # Skip this bank if token retrieval fails
                pass

        # If no real accounts but have linked accounts, generate demo accounts
        if len(all_accounts) == 0:
            linked_accounts = AccountLinkingService.get_linked_accounts(client_id)
            if linked_accounts:
                for acc in linked_accounts:
                    # Only generate demo for banks that were requested
                    if acc['bank'] in bank_codes:
                        demo_account = Account(
                            account_id=acc['account_number'],
                            bank=acc['bank'],
                            currency="RUB",
                            account_type="current",
                            nickname=acc.get('nickname', f"Счет {acc['account_number'][-4:]}")
                        )
                        all_accounts.append(demo_account)

        return all_accounts

    @staticmethod
    async def get_balances(
        client_id: str,
        account_ids: Optional[list[str]] = None,
        bank_codes: Optional[list[str]] = None,
    ) -> list[Balance]:
        """Aggregate balances for accounts.

        Args:
            client_id: Client ID
            account_ids: Specific account IDs to query (None = all accounts)
            bank_codes: List of bank codes to query (None = all banks)

        Returns:
            List of normalized balances
        """
        # Get accounts from API
        all_accounts = await AggregationService.get_accounts(client_id, bank_codes)
        
        # Also get linked accounts - they may have account_number that we can use directly
        import logging
        logger_bal = logging.getLogger(__name__)
        linked_accounts = AccountLinkingService.get_linked_accounts(client_id)
        logger_bal.info(f"Got {len(all_accounts)} accounts from API and {len(linked_accounts)} linked accounts for balances")
        
        # Build account_ids list from API accounts
        api_account_ids = [acc.account_id for acc in all_accounts]
        
        # Also add account_numbers from linked accounts that have account_id set
        # If linked account has account_id, use it; if not, use account_number as account_id
        linked_account_ids = []
        for linked_acc in linked_accounts:
            if linked_acc.get('account_id'):
                linked_account_ids.append(linked_acc['account_id'])
            else:
                # Use account_number as account_id for direct API queries
                linked_account_ids.append(linked_acc['account_number'])
        
        # Combine API account IDs and linked account IDs
        if account_ids is None:
            # Use all available account IDs (from API and linked accounts)
            account_ids = list(set(api_account_ids + linked_account_ids))
        else:
            # Filter to only requested account_ids
            account_ids = [acc_id for acc_id in account_ids if acc_id in api_account_ids or acc_id in linked_account_ids]

        all_balances: list[Balance] = []

        # Group accounts by bank
        # First, use accounts from API
        accounts_by_bank: dict[str, list[str]] = {}
        for account in all_accounts:
            if account.account_id in account_ids:
                if account.bank not in accounts_by_bank:
                    accounts_by_bank[account.bank] = []
                accounts_by_bank[account.bank].append(account.account_id)
        
        # Also add linked accounts - use their bank and account_number/account_id
        for linked_acc in linked_accounts:
            bank_code = linked_acc['bank']
            acc_id = linked_acc.get('account_id') or linked_acc['account_number']
            if acc_id in account_ids:
                if bank_code not in accounts_by_bank:
                    accounts_by_bank[bank_code] = []
                if acc_id not in accounts_by_bank[bank_code]:
                    accounts_by_bank[bank_code].append(acc_id)
                    logger_bal.info(f"Added linked account {acc_id} from {bank_code} to balances query")

        # Get balances for each bank
        # Note: We assume consent was already created in get_accounts step
        # If consent is missing, we'll get 403 and skip this account
        for bank_code, acc_ids in accounts_by_bank.items():
            # Check if credentials are available
            if not _has_bank_credentials(bank_code):
                continue
                
            try:
                # Step 1: Get bank token with timeout protection
                try:
                    token_data = await asyncio.wait_for(
                        TokenService.get_bank_token(bank_code),
                        timeout=5.0  # 5 second timeout per bank
                    )
                    bank_token = token_data["access_token"]
                except asyncio.TimeoutError:
                    # Skip this bank if token request times out
                    continue

                client = get_bank_client(bank_code)
                try:
                    # Step 3: Get balances (interbank request)
                    # GET /accounts/{id}/balances?client_id=team268-1
                    # Headers: Authorization: Bearer <bank_token>, X-Requesting-Bank: team268
                    # Note: X-Consent-Id should be included if consent was created
                    # Get consent_id if available (was created when getting accounts)
                    consent_id = ConsentService.get_consent_id(client_id, bank_code)
                    if consent_id:
                        logger_bal.info(f"✅ Found consent_id={consent_id} for {bank_code}, client_id={client_id}")
                    else:
                        logger_bal.warning(f"⚠️ No consent_id found for {bank_code}, client_id={client_id} - will try to create one")
                    logger_bal.info(f"Getting balances from {bank_code} for {len(acc_ids)} accounts, consent_id={'present' if consent_id else 'missing'}")
                    
                    # If no consent_id, try to create consent (should have been created in get_accounts, but just in case)
                    if not consent_id:
                        logger_bal.warning(f"No consent_id found for {bank_code}, attempting to create consent")
                        try:
                            consent_response = await ConsentService.request_accounts_consent(
                                bank_code=bank_code,
                                client_id=client_id,
                                permissions=["ReadAccountsDetail", "ReadBalances", "ReadTransactions"],
                            )
                            consent_id = consent_response.get("consent_id")
                            if consent_id:
                                logger_bal.info(f"Created consent for {bank_code}, consent_id={consent_id}")
                        except Exception as e:
                            logger_bal.error(f"Failed to create consent for {bank_code}: {e}")
                    
                    for account_id in acc_ids:
                        try:
                            logger_bal.info(f"🔍 Requesting balances for account {account_id} from {bank_code} with consent_id={consent_id}")
                            balances_response = await asyncio.wait_for(
                                client.get_balances(
                                    bank_token=bank_token,
                                    account_id=account_id,
                                    client_id=client_id,
                                    requesting_bank=settings.requesting_bank_id,  # team268 (without suffix)
                                    consent_id=consent_id,  # Pass consent_id if available
                                ),
                                timeout=10.0  # Увеличено с 5 до 10 секунд
                            )

                            # API may return balances in data.balances or data.balance
                            # Handle both formats: {"data": {"balances": [...]}} and {"balances": [...]}
                            data_section = balances_response.get("data", {})
                            if isinstance(data_section, dict):
                                balances_list = data_section.get("balances", data_section.get("balance", []))
                                # If balance is a single dict, wrap it in a list
                                if isinstance(balances_list, dict):
                                    balances_list = [balances_list]
                            else:
                                balances_list = balances_response.get("balances", [])
                            
                            # Ensure balances_list is a list
                            if not isinstance(balances_list, list):
                                balances_list = []
                            
                            logger_bal.info(f"Got {len(balances_list)} balances for account {account_id} from {bank_code} (consent_id={'present' if consent_id else 'missing'})")
                            if len(balances_list) == 0:
                                logger_bal.warning(f"No balances returned for account {account_id} from {bank_code} - full response: {balances_response}")
                            for balance_data in balances_list:
                                # Log raw balance data for debugging
                                logger_bal.debug(f"Raw balance_data for {account_id}: {balance_data}")
                                normalized = AggregationService._normalize_balance(
                                    balance_data, account_id
                                )
                                all_balances.append(normalized)
                                logger_bal.info(f"✅ REAL Balance for {account_id}: amount={normalized.amount}, currency={normalized.currency}, type={normalized.balance_type}")
                        except ConsentRequiredError:
                            # Consent required - try to create consent if not already created
                            logger_bal.warning(f"Consent required for balances from {bank_code}, account {account_id}")
                            if not consent_id:
                                try:
                                    consent_response = await ConsentService.request_accounts_consent(
                                        bank_code=bank_code,
                                        client_id=client_id,
                                        permissions=["ReadBalances"],
                                    )
                                    consent_id = consent_response.get("consent_id")
                                    if consent_id:
                                        # Retry with consent_id
                                        balances_response = await client.get_balances(
                                            bank_token=bank_token,
                                            account_id=account_id,
                                            client_id=client_id,
                                            requesting_bank=settings.requesting_bank_id,
                                            consent_id=consent_id,
                                        )
                                        # API may return balances in data.balances or data.balance
                                        data_section = balances_response.get("data", {})
                                        if isinstance(data_section, dict):
                                            balances_list = data_section.get("balances", data_section.get("balance", []))
                                            if isinstance(balances_list, dict):
                                                balances_list = [balances_list]
                                        else:
                                            balances_list = balances_response.get("balances", [])
                                        
                                        if not isinstance(balances_list, list):
                                            balances_list = []
                                        
                                        if len(balances_list) > 0:
                                            for balance_data in balances_list:
                                                normalized = AggregationService._normalize_balance(
                                                    balance_data, account_id
                                                )
                                                all_balances.append(normalized)
                                                logger_bal.info(f"✅ REAL Balance for {account_id}: {normalized.amount} {normalized.currency}")
                                except Exception as e2:
                                    logger_bal.error(f"Failed to create consent and retry: {e2}")
                        except asyncio.TimeoutError:
                            logger_bal.error(f"⏱️ Timeout getting balances for account {account_id} from {bank_code} (timeout=10s)")
                            pass
                        except Exception as e:
                            # Skip this account if request fails
                            logger_bal.error(f"❌ Error getting balances for account {account_id} from {bank_code}: {type(e).__name__}: {e}", exc_info=True)
                            pass
                finally:
                    await client.close()
            except Exception:
                # Skip this bank if token retrieval fails
                pass

        # IMPORTANT: Only generate demo balances if:
        # 1. We got NO balances from API (all_balances is empty)
        # 2. AND we have NO real accounts from API (API returned 0 accounts)
        # 3. AND we have linked accounts (user manually linked accounts)
        # In this case, we generate demo data because we can't get real data from API
        if len(all_balances) == 0:
            # Check if we got real accounts from API
            has_real_accounts_from_api = len(all_accounts) > 0
            
            if not has_real_accounts_from_api and len(linked_accounts) > 0:
                # No real accounts from API but have linked accounts - generate demo data
                logger_bal.info(f"No real accounts from API, but have {len(linked_accounts)} linked accounts - generating demo balances")
                for acc in linked_accounts:
                    # Only generate demo for accounts that were requested
                    if account_ids is None or acc['account_number'] in account_ids or (acc.get('account_id') and acc['account_id'] in account_ids):
                        demo_balance = Balance(
                            account_id=acc.get('account_id') or acc['account_number'],
                            amount="50000.00",
                            currency="RUB",
                            balance_type="interimBooked"
                        )
                        all_balances.append(demo_balance)
            elif has_real_accounts_from_api:
                # We have real accounts but no balances - this indicates an error getting balances
                logger_bal.warning(f"Have {len(all_accounts)} real accounts from API but got 0 balances - this indicates an error getting balances, NOT generating demo data")
            else:
                # No accounts, no linked accounts - nothing to show
                logger_bal.info(f"No accounts from API and no linked accounts - returning empty balances")

        return all_balances

    @staticmethod
    async def get_transactions(
        client_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        account_ids: Optional[list[str]] = None,
        bank_codes: Optional[list[str]] = None,
    ) -> list[Transaction]:
        """Aggregate transactions from all accounts.

        Args:
            client_id: Client ID
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: now)
            account_ids: Specific account IDs to query (None = all accounts)
            bank_codes: List of bank codes to query (None = all banks)

        Returns:
            List of normalized transactions
        """
        if from_date is None:
            from_date = datetime.now() - timedelta(days=30)
        if to_date is None:
            to_date = datetime.now()

        # Get accounts from API
        all_accounts = await AggregationService.get_accounts(client_id, bank_codes)
        
        # Also get linked accounts - they may have account_number that we can use directly
        import logging
        logger_txn = logging.getLogger(__name__)
        linked_accounts = AccountLinkingService.get_linked_accounts(client_id)
        logger_txn.info(f"Got {len(all_accounts)} accounts from API and {len(linked_accounts)} linked accounts for transactions")
        
        # Build account_ids list from API accounts
        api_account_ids = [acc.account_id for acc in all_accounts]
        
        # Also add account_numbers from linked accounts
        linked_account_ids = []
        for linked_acc in linked_accounts:
            if linked_acc.get('account_id'):
                linked_account_ids.append(linked_acc['account_id'])
            else:
                # Use account_number as account_id for direct API queries
                linked_account_ids.append(linked_acc['account_number'])
        
        # Combine API account IDs and linked account IDs
        if account_ids is None:
            # Use all available account IDs (from API and linked accounts)
            account_ids = list(set(api_account_ids + linked_account_ids))
        else:
            # Filter to only requested account_ids
            account_ids = [acc_id for acc_id in account_ids if acc_id in api_account_ids or acc_id in linked_account_ids]

        all_transactions: list[Transaction] = []

        # Group accounts by bank
        # First, use accounts from API
        accounts_by_bank: dict[str, list[str]] = {}
        for account in all_accounts:
            if account.account_id in account_ids:
                if account.bank not in accounts_by_bank:
                    accounts_by_bank[account.bank] = []
                accounts_by_bank[account.bank].append(account.account_id)
        
        # Also add linked accounts - use their bank and account_number/account_id
        for linked_acc in linked_accounts:
            bank_code = linked_acc['bank']
            acc_id = linked_acc.get('account_id') or linked_acc['account_number']
            if acc_id in account_ids:
                if bank_code not in accounts_by_bank:
                    accounts_by_bank[bank_code] = []
                if acc_id not in accounts_by_bank[bank_code]:
                    accounts_by_bank[bank_code].append(acc_id)
                    logger_txn.info(f"Added linked account {acc_id} from {bank_code} to transactions query")

        # Get transactions for each bank
        for bank_code, acc_ids in accounts_by_bank.items():
            # Check if credentials are available
            if not _has_bank_credentials(bank_code):
                continue
                
            try:
                # Step 1: Get bank token with timeout protection
                try:
                    token_data = await asyncio.wait_for(
                        TokenService.get_bank_token(bank_code),
                        timeout=5.0  # 5 second timeout per bank
                    )
                    bank_token = token_data["access_token"]
                except asyncio.TimeoutError:
                    # Skip this bank if token request times out
                    continue

                client = get_bank_client(bank_code)
                try:
                    # Step 3: Get transactions (interbank request)
                    # GET /accounts/{id}/transactions?client_id=team268-1&from_booking_date_time=...&to_booking_date_time=...
                    # Headers: Authorization: Bearer <bank_token>, X-Requesting-Bank: team268, X-Consent-Id: <consent_id>
                    # Note: Consent should be created in get_accounts step above
                    # Get consent_id if available (was created when getting accounts)
                    consent_id = ConsentService.get_consent_id(client_id, bank_code)
                    logger_txn.info(f"Getting transactions from {bank_code} for {len(acc_ids)} accounts, consent_id={'present' if consent_id else 'missing'}, from_date={from_date.isoformat()}, to_date={to_date.isoformat()}")
                    
                    for account_id in acc_ids:
                        try:
                            transactions_response = await client.get_transactions(
                                bank_token=bank_token,
                                account_id=account_id,
                                client_id=client_id,
                                requesting_bank=settings.requesting_bank_id,  # team268 (without suffix)
                                from_booking_date_time=from_date.isoformat(),
                                to_booking_date_time=to_date.isoformat(),
                                consent_id=consent_id,  # Pass consent_id if available
                            )

                            # API may return transactions in data.transactions or data.transaction
                            # Handle both formats: {"data": {"transactions": [...]}} and {"transactions": [...]}
                            data_section = transactions_response.get("data", {})
                            if isinstance(data_section, dict):
                                transactions_list = data_section.get("transactions", data_section.get("transaction", []))
                                # If transaction is a single dict, wrap it in a list
                                if isinstance(transactions_list, dict):
                                    transactions_list = [transactions_list]
                            else:
                                transactions_list = transactions_response.get("transactions", [])
                            
                            # Ensure transactions_list is a list
                            if not isinstance(transactions_list, list):
                                transactions_list = []
                            
                            logger_txn.info(f"Got {len(transactions_list)} transactions for account {account_id} from {bank_code}")
                            for transaction_data in transactions_list:
                                normalized = (
                                    AggregationService._normalize_transaction(
                                        transaction_data, account_id
                                    )
                                )
                                all_transactions.append(normalized)
                        except ConsentRequiredError as e:
                            # Consent required for transactions - try to create consent if not already created
                            logger_txn.warning(f"Consent required for transactions from {bank_code}, account {account_id} (current consent_id: {consent_id})")
                            if not consent_id:
                                try:
                                    # Create consent with ReadTransactions permission
                                    consent_response = await ConsentService.request_accounts_consent(
                                        bank_code=bank_code,
                                        client_id=client_id,
                                        permissions=["ReadTransactions"],
                                    )
                                    consent_id = consent_response.get("consent_id")
                                    if consent_id:
                                        # Retry with new consent_id
                                        logger_txn.info(f"Created new consent for transactions: {consent_id}, retrying...")
                                        try:
                                            transactions_response = await client.get_transactions(
                                                bank_token=bank_token,
                                                account_id=account_id,
                                                client_id=client_id,
                                                requesting_bank=settings.requesting_bank_id,
                                                from_booking_date_time=from_date.isoformat(),
                                                to_booking_date_time=to_date.isoformat(),
                                                consent_id=consent_id,
                                            )
                                            # Parse transactions response
                                            data_section = transactions_response.get("data", {})
                                            if isinstance(data_section, dict):
                                                transactions_list = data_section.get("transactions", data_section.get("transaction", []))
                                                if isinstance(transactions_list, dict):
                                                    transactions_list = [transactions_list]
                                            else:
                                                transactions_list = transactions_response.get("transactions", [])
                                            
                                            if not isinstance(transactions_list, list):
                                                transactions_list = []
                                            
                                            for transaction_data in transactions_list:
                                                normalized = AggregationService._normalize_transaction(
                                                    transaction_data, account_id
                                                )
                                                all_transactions.append(normalized)
                                                logger_txn.info(f"✅ REAL Transaction for {account_id}: {normalized.amount} {normalized.currency}")
                                        except Exception as e2:
                                            logger_txn.error(f"Error retrying transactions with new consent: {e2}")
                                except Exception as e2:
                                    logger_txn.error(f"Failed to create consent for transactions: {e2}")
                        except Exception as e:
                            # Skip this account if request fails
                            logger_txn.error(f"Error getting transactions for account {account_id} from {bank_code}: {e}", exc_info=True)
                            pass
                finally:
                    await client.close()
            except Exception:
                # Skip this bank if token retrieval fails
                pass

        return all_transactions
