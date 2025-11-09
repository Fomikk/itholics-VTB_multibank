"""Service for managing linked bank accounts."""
from typing import Optional
from datetime import datetime
from app.core.types import Account


class AccountLinkingService:
    """Service for managing linked bank accounts."""
    
    # In-memory storage (in production, use database)
    _linked_accounts: dict[str, list[dict]] = {}
    
    @staticmethod
    def link_account(
        client_id: str,
        bank: str,
        account_number: str,
        account_id: Optional[str] = None,
        nickname: Optional[str] = None,
    ) -> dict:
        """Link a bank account to a client.
        
        Args:
            client_id: Client ID
            bank: Bank code (vbank, abank, sbank)
            account_number: Account number or identifier
            account_id: Optional account ID from bank API
            nickname: Optional nickname for the account
            
        Returns:
            Linked account information
        """
        if client_id not in AccountLinkingService._linked_accounts:
            AccountLinkingService._linked_accounts[client_id] = []
        
        linked_account = {
            "id": f"{bank}-{account_number}",
            "bank": bank,
            "account_number": account_number,
            "account_id": account_id,
            "nickname": nickname or f"{bank.upper()} Account",
            "linked_at": datetime.now().isoformat(),
            "active": True,
        }
        
        # Check if already exists
        existing = next(
            (acc for acc in AccountLinkingService._linked_accounts[client_id] 
             if acc["id"] == linked_account["id"]),
            None
        )
        
        if existing:
            # Update existing
            existing.update(linked_account)
            return existing
        else:
            # Add new
            AccountLinkingService._linked_accounts[client_id].append(linked_account)
            return linked_account
    
    @staticmethod
    def get_linked_accounts(client_id: str) -> list[dict]:
        """Get all linked accounts for a client.
        
        Args:
            client_id: Client ID
            
        Returns:
            List of linked accounts
        """
        return AccountLinkingService._linked_accounts.get(client_id, [])
    
    @staticmethod
    def unlink_account(client_id: str, account_id: str) -> bool:
        """Unlink a bank account.
        
        Args:
            client_id: Client ID
            account_id: Account ID to unlink
            
        Returns:
            True if account was unlinked, False if not found
        """
        if client_id not in AccountLinkingService._linked_accounts:
            return False
        
        accounts = AccountLinkingService._linked_accounts[client_id]
        initial_count = len(accounts)
        AccountLinkingService._linked_accounts[client_id] = [
            acc for acc in accounts if acc["id"] != account_id
        ]
        
        return len(AccountLinkingService._linked_accounts[client_id]) < initial_count
    
    @staticmethod
    def get_banks_for_client(client_id: str) -> list[str]:
        """Get list of banks that have linked accounts for a client.
        
        Args:
            client_id: Client ID
            
        Returns:
            List of bank codes
        """
        accounts = AccountLinkingService.get_linked_accounts(client_id)
        banks = set(acc["bank"] for acc in accounts if acc["active"])
        return list(banks)

