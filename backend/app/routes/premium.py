from fastapi import APIRouter

from ..premium_utils import calculate_premium as compute_premium
from ..schemas import PremiumCalculateRequest, PremiumCalculateResponse

router = APIRouter(prefix="/api/premium", tags=["premium"])

@router.post("/calculate", response_model=PremiumCalculateResponse)
def calculate_premium(request: PremiumCalculateRequest):
    premium = compute_premium(request.income, request.risk_preference, request.income_variance or 0)
    return PremiumCalculateResponse(premium=premium)