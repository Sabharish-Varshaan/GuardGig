from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..trigger_utils import evaluate_rain_trigger, fetch_aqi, fetch_rain_mm

router = APIRouter(prefix="/api/trigger", tags=["trigger"])

class TriggerCheckRequest(BaseModel):
    location: str

class TriggerCheckResponse(BaseModel):
    trigger: str
    rain_mm: float
    aqi: float | None

@router.post("/check", response_model=TriggerCheckResponse)
async def check_trigger(request: TriggerCheckRequest):
    try:
        rain = await fetch_rain_mm(request.location)
        aqi = await fetch_aqi(request.location)
        trigger = evaluate_rain_trigger(rain)
        return TriggerCheckResponse(trigger=trigger, rain_mm=rain, aqi=aqi)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))