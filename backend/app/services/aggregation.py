"""Service for aggregating data from multiple banks."""
from datetime import datetime, timedelta
from typing import Any, Optional
from app.clients.factory import get_all_bank_clients, get_bank_client
from app.core.exceptions import ConsentRequiredError
from app.core.types import Account, Balance, Transaction
from app.services.consent_service import ConsentService
from app.services.token_service import TokenService
from app.settings import settings


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
        return Account(
            account_id=account_data.get("account_id", ""),
            bank=bank_code,
            currency=account_data.get("currency", "RUB"),
            account_type=account_data.get("account_type", "Personal"),
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
        return Balance(
            account_id=account_id,
            amount=str(balance_data.get("amount", "0")),
            currency=balance_data.get("currency", "RUB"),
            balance_type=balance_data.get("balance_type", "interimBooked"),
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
        return Transaction(
            transaction_id=transaction_data.get("transaction_id", ""),
            account_id=account_id,
            amount=str(transaction_data.get("amount", "0")),
            currency=transaction_data.get("currency", "RUB"),
            booking_date=transaction_data.get("booking_date_time", ""),
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
            bank_codes: List of bank codes to query (None = all banks)

        Returns:
            List of normalized accounts
        """
        if bank_codes is None:
            bank_codes = ["vbank", "abank", "sbank"]

        all_accounts: list[Account] = []

        for bank_code in bank_codes:
            try:
                # Get bank token
                token_data = await TokenService.get_bank_token(bank_code)
                bank_token = token_data["access_token"]

                client = get_bank_client(bank_code)
                try:
                    # Try to get accounts
                    accounts_response = await client.get_accounts(
                        bank_token=bank_token,
                        client_id=client_id,
                        requesting_bank=settings.requesting_bank_id,
                    )

                    # Normalize accounts
                    accounts_list = accounts_response.get("accounts", [])
                    if isinstance(accounts_list, list):
                        for account_data in accounts_list:
                            normalized = AggregationService._normalize_account(
                                account_data, bank_code
                            )
                            all_accounts.append(normalized)

                except ConsentRequiredError:
                    # Try to create consent and retry once
                    try:
                        consent_response = await ConsentService.request_accounts_consent(
                            bank_code=bank_code,
                            client_id=client_id,
                        )
                        consent_id = consent_response.get("consent_id")

                        if consent_id:
                            # Retry with consent
                            accounts_response = await client.get_accounts(
                                bank_token=bank_token,
                                client_id=client_id,
                                requesting_bank=settings.requesting_bank_id,
                                consent_id=consent_id,
                            )

                            accounts_list = accounts_response.get("accounts", [])
                            if isinstance(accounts_list, list):
                                for account_data in accounts_list:
                                    normalized = AggregationService._normalize_account(
                                        account_data, bank_code
                                    )
                                    all_accounts.append(normalized)
                    except Exception:
                        # Skip this bank if consent creation fails
                        pass
                except Exception:
                    # Skip this bank if request fails
                    pass
                finally:
                    await client.close()

            except Exception:
                # Skip this bank if token retrieval fails
                pass

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
        # Get accounts
        all_accounts = await AggregationService.get_accounts(client_id, bank_codes)
        
        # Filter by account_ids if specified
        if account_ids is None:
            account_ids = [acc.account_id for acc in all_accounts]

        all_balances: list[Balance] = []

        # Group accounts by bank
        accounts_by_bank: dict[str, list[str]] = {}
        for account in all_accounts:
            if account.account_id in account_ids:
                if account.bank not in accounts_by_bank:
                    accounts_by_bank[account.bank] = []
                accounts_by_bank[account.bank].append(account.account_id)

        # Get balances for each bank
        for bank_code, acc_ids in accounts_by_bank.items():
            try:
                token_data = await TokenService.get_bank_token(bank_code)
                bank_token = token_data["access_token"]

                client = get_bank_client(bank_code)
                try:
                    for account_id in acc_ids:
                        try:
                            balances_response = await client.get_balances(
                                bank_token=bank_token,
                                account_id=account_id,
                                client_id=client_id,
                                requesting_bank=settings.requesting_bank_id,
                            )

                            balances_list = balances_response.get("balances", [])
                            if isinstance(balances_list, list):
                                for balance_data in balances_list:
                                    normalized = AggregationService._normalize_balance(
                                        balance_data, account_id
                                    )
                                    all_balances.append(normalized)
                        except Exception:
                            # Skip this account if request fails
                            pass
                finally:
                    await client.close()
            except Exception:
                # Skip this bank if token retrieval fails
                pass

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

        # Get accounts
        all_accounts = await AggregationService.get_accounts(client_id, bank_codes)
        
        # Filter by account_ids if specified
        if account_ids is None:
            account_ids = [acc.account_id for acc in all_accounts]

        all_transactions: list[Transaction] = []

        # Group accounts by bank
        accounts_by_bank: dict[str, list[str]] = {}
        for account in all_accounts:
            if account.account_id in account_ids:
                if account.bank not in accounts_by_bank:
                    accounts_by_bank[account.bank] = []
                accounts_by_bank[account.bank].append(account.account_id)

        # Get transactions for each bank
        for bank_code, acc_ids in accounts_by_bank.items():
            try:
                token_data = await TokenService.get_bank_token(bank_code)
                bank_token = token_data["access_token"]

                client = get_bank_client(bank_code)
                try:
                    for account_id in acc_ids:
                        try:
                            transactions_response = await client.get_transactions(
                                bank_token=bank_token,
                                account_id=account_id,
                                client_id=client_id,
                                requesting_bank=settings.requesting_bank_id,
                                from_booking_date_time=from_date.isoformat(),
                                to_booking_date_time=to_date.isoformat(),
                            )

                            transactions_list = transactions_response.get(
                                "transactions", []
                            )
                            if isinstance(transactions_list, list):
                                for transaction_data in transactions_list:
                                    normalized = (
                                        AggregationService._normalize_transaction(
                                            transaction_data, account_id
                                        )
                                    )
                                    all_transactions.append(normalized)
                        except Exception:
                            # Skip this account if request fails
                            pass
                finally:
                    await client.close()
            except Exception:
                # Skip this bank if token retrieval fails
                pass

        return all_transactions
