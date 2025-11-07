"""Bank-related API endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["banks"])

# TODO: Implement endpoints
# - POST /api/tokens/{bank}
# - POST /api/consents/accounts
# - GET /api/accounts/aggregate
# - GET /api/transactions/aggregate
# - GET /api/analytics/summary
# - POST /api/cashback/activate

