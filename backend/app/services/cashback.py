"""Cashback service for managing cashback bonuses."""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel


class CashbackBonus(BaseModel):
    """Cashback bonus model."""

    client_id: str
    category: str
    bonus_percent: float
    valid_until: datetime
    activated_at: datetime


class CashbackService:
    """Service for managing cashback bonuses."""

    # In-memory storage (in production, use database)
    _bonuses: dict[str, list[CashbackBonus]] = {}

    @staticmethod
    def activate_cashback(
        client_id: str,
        category: str,
        bonus_percent: float,
        valid_until: Optional[datetime] = None,
    ) -> CashbackBonus:
        """Activate cashback bonus for a category.

        Args:
            client_id: Client ID
            category: Spending category (e.g., "groceries", "restaurants")
            bonus_percent: Bonus percentage (e.g., 5.0 for 5%)
            valid_until: Expiration date (default: 30 days from now)

        Returns:
            Created cashback bonus
        """
        if valid_until is None:
            valid_until = datetime.now() + timedelta(days=30)

        bonus = CashbackBonus(
            client_id=client_id,
            category=category,
            bonus_percent=bonus_percent,
            valid_until=valid_until,
            activated_at=datetime.now(),
        )

        if client_id not in CashbackService._bonuses:
            CashbackService._bonuses[client_id] = []

        CashbackService._bonuses[client_id].append(bonus)
        return bonus

    @staticmethod
    def get_active_bonuses(client_id: str) -> list[CashbackBonus]:
        """Get active cashback bonuses for a client.

        Args:
            client_id: Client ID

        Returns:
            List of active bonuses
        """
        if client_id not in CashbackService._bonuses:
            return []

        now = datetime.now()
        active = [
            bonus
            for bonus in CashbackService._bonuses[client_id]
            if bonus.valid_until > now
        ]

        return active

    @staticmethod
    def get_bonus_for_category(
        client_id: str, category: str
    ) -> Optional[CashbackBonus]:
        """Get active bonus for a specific category.

        Args:
            client_id: Client ID
            category: Spending category

        Returns:
            Active bonus if exists, None otherwise
        """
        active_bonuses = CashbackService.get_active_bonuses(client_id)
        for bonus in active_bonuses:
            if bonus.category.lower() == category.lower():
                return bonus
        return None
