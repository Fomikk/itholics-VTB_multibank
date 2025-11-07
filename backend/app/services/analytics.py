"""Analytics service for financial data analysis."""
from datetime import datetime, timedelta
from typing import Any
from collections import defaultdict
from app.services.aggregation import AggregationService


class AnalyticsService:
    """Service for financial analytics."""

    @staticmethod
    async def get_summary(
        client_id: str, period_days: int = 30
    ) -> dict[str, Any]:
        """Get financial summary for dashboard.

        Args:
            client_id: Client ID
            period_days: Number of days to analyze

        Returns:
            Summary with net worth, spending by category, top expenses, etc.
        """
        # Get accounts and balances
        accounts = await AggregationService.get_accounts(client_id)
        balances = await AggregationService.get_balances(client_id)

        # Calculate net worth
        net_worth = 0.0
        balances_by_account: dict[str, float] = {}
        for balance in balances:
            try:
                amount = float(balance.amount)
                if balance.account_id not in balances_by_account:
                    balances_by_account[balance.account_id] = 0.0
                balances_by_account[balance.account_id] += amount
            except (ValueError, TypeError):
                pass

        net_worth = sum(balances_by_account.values())

        # Get transactions
        from_date = datetime.now() - timedelta(days=period_days)
        transactions = await AggregationService.get_transactions(
            client_id, from_date=from_date
        )

        # Calculate spending by category
        spending_by_category: dict[str, float] = defaultdict(float)
        total_spending = 0.0

        for transaction in transactions:
            try:
                amount = float(transaction.amount)
                if amount < 0:  # Only expenses
                    category = AnalyticsService._categorize_transaction(transaction)
                    spending_by_category[category] += abs(amount)
                    total_spending += abs(amount)
            except (ValueError, TypeError):
                pass

        # Get top expenses
        top_expenses = sorted(
            [
                {"category": cat, "amount": amount}
                for cat, amount in spending_by_category.items()
            ],
            key=lambda x: x["amount"],
            reverse=True,
        )[:5]

        # Calculate weekly spending trend
        weekly_trend = AnalyticsService._calculate_weekly_trend(transactions)

        return {
            "net_worth": net_worth,
            "total_accounts": len(accounts),
            "total_spending": total_spending,
            "spending_by_category": dict(spending_by_category),
            "top_expenses": top_expenses,
            "weekly_trend": weekly_trend,
            "period_days": period_days,
        }

    @staticmethod
    def _categorize_transaction(transaction: Any) -> str:
        """Categorize transaction based on description or MCC.

        Args:
            transaction: Transaction object

        Returns:
            Category name
        """
        description = (transaction.description or "").lower()
        mcc = transaction.mcc or ""

        # MCC-based categorization
        if mcc:
            mcc_int = int(mcc) if mcc.isdigit() else 0
            if 5411 <= mcc_int <= 5412:  # Grocery stores
                return "groceries"
            elif 5812 <= mcc_int <= 5814:  # Restaurants
                return "restaurants"
            elif 5541 <= mcc_int <= 5542:  # Gas stations
                return "gas"
            elif 5912 <= mcc_int <= 5912:  # Pharmacies
                return "pharmacy"
            elif 5311 <= mcc_int <= 5311:  # Department stores
                return "shopping"

        # Description-based categorization
        if any(word in description for word in ["магазин", "store", "супермаркет"]):
            return "groceries"
        elif any(word in description for word in ["ресторан", "кафе", "restaurant", "cafe"]):
            return "restaurants"
        elif any(word in description for word in ["заправка", "gas", "бензин"]):
            return "gas"
        elif any(word in description for word in ["аптека", "pharmacy"]):
            return "pharmacy"
        elif any(word in description for word in ["транспорт", "transport", "метро", "metro"]):
            return "transport"
        elif any(word in description for word in ["развлечения", "entertainment", "кино", "cinema"]):
            return "entertainment"

        return "other"

    @staticmethod
    def _calculate_weekly_trend(transactions: list[Any]) -> list[dict[str, Any]]:
        """Calculate weekly spending trend.

        Args:
            transactions: List of transactions

        Returns:
            List of weekly spending data
        """
        weekly_spending: dict[str, float] = defaultdict(float)

        for transaction in transactions:
            try:
                amount = float(transaction.amount)
                if amount < 0:  # Only expenses
                    booking_date = datetime.fromisoformat(
                        transaction.booking_date.replace("Z", "+00:00")
                    )
                    week_start = booking_date - timedelta(
                        days=booking_date.weekday()
                    )
                    week_key = week_start.strftime("%Y-%m-%d")
                    weekly_spending[week_key] += abs(amount)
            except (ValueError, TypeError, AttributeError):
                pass

        # Convert to list sorted by date
        trend = [
            {"week": week, "spending": spending}
            for week, spending in sorted(weekly_spending.items())
        ]

        return trend

