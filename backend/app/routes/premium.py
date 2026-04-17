from fastapi import APIRouter

from ..premium_utils import calculate_pricing_details
from ..schemas import PremiumCalculateRequest, PremiumCalculateResponse

router = APIRouter(prefix="/api/premium", tags=["premium"])

@router.post("/calculate", response_model=PremiumCalculateResponse)
def calculate_premium(request: PremiumCalculateRequest):
    pricing = calculate_pricing_details(
        income=request.income,
        income_variance=request.income_variance or 0,
        city=request.city,
        lat=request.lat,
        lon=request.lon,
        forecast_data=request.forecast_data,
    )
    return PremiumCalculateResponse(
        premium=pricing["premium"],
        coverage=pricing["coverage"],
        coverage_percentage=pricing["coverage_percentage"],
        target=pricing["target"],
        reason=pricing["reason"],
    )