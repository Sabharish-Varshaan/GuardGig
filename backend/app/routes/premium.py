from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/premium", tags=["premium"])

class PremiumCalculateRequest(BaseModel):
    income: float
    location: str
    weather: str

class PremiumCalculateResponse(BaseModel):
    premium: float

def calculate_base(income: float) -> float:
    """Calculate base premium as 1% of income."""
    return income * 0.01

def calculate_risk(location: str) -> float:
    """Calculate risk based on location."""
    # Simple location-based risk
    risk_factors = {
        "urban": 50,
        "suburban": 30,
        "rural": 20
    }
    return risk_factors.get(location.lower(), 25)

def calculate_event(weather: str) -> float:
    """Calculate event risk based on weather."""
    # Simple weather-based event risk
    event_factors = {
        "sunny": 10,
        "rainy": 20,
        "stormy": 50,
        "snowy": 30
    }
    return event_factors.get(weather.lower(), 15)

@router.post("/calculate", response_model=PremiumCalculateResponse)
def calculate_premium(request: PremiumCalculateRequest):
    try:
        base = calculate_base(request.income)
        risk = calculate_risk(request.location)
        event = calculate_event(request.weather)
        premium = base + risk + event
        return PremiumCalculateResponse(premium=round(premium, 2))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))