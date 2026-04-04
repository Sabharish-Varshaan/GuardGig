from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ml.predict import get_risk_score, get_fraud_score

router = APIRouter(prefix="/api/ml", tags=["ml"])


class MLScoreRequest(BaseModel):
    # Risk features
    mean_income: Optional[float] = Field(None, description="mean income (daily)")
    income_variance: Optional[float] = 0.0
    rain: Optional[float] = 0.0
    aqi: Optional[float] = 0.0

    # Fraud features
    number_of_claims_today: Optional[int] = 0
    time_since_last_claim: Optional[float] = 0.0
    location_change: Optional[float] = 0.0
    activity_status: Optional[str] = "active"


class MLScoreResponse(BaseModel):
    risk_score: float
    fraud_score: float


@router.post("/score", response_model=MLScoreResponse)
def score(payload: MLScoreRequest):
    try:
        risk_features = {
            "mean_income": payload.mean_income or 0.0,
            "income_variance": float(payload.income_variance or 0.0),
            "rain": float(payload.rain or 0.0),
            "aqi": float(payload.aqi or 0.0),
        }

        fraud_features = {
            "number_of_claims_today": int(payload.number_of_claims_today or 0),
            "time_since_last_claim": float(payload.time_since_last_claim or 0.0),
            "location_change": float(payload.location_change or 0.0),
            "activity_status": str(payload.activity_status or "active"),
        }

        risk_score = get_risk_score(risk_features)
        fraud_score = get_fraud_score(fraud_features)

        return MLScoreResponse(risk_score=float(risk_score), fraud_score=float(fraud_score))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
