from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from ..trigger_utils import check_trigger as evaluate_trigger, fetch_trigger_snapshot

router = APIRouter(prefix="/api/trigger", tags=["trigger"])

class TriggerCheckRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    location: str | None = None
    lat: float | None = None
    lon: float | None = None


class TriggerDecision(BaseModel):
    trigger: bool
    type: str | None = None
    severity: str | None = None

class TriggerCheckResponse(BaseModel):
    rain: float
    aqi: float
    trigger: TriggerDecision

@router.post("/check", response_model=TriggerCheckResponse)
async def check_trigger(request: TriggerCheckRequest):
    try:
        rain, aqi = await fetch_trigger_snapshot(request.location, request.lat, request.lon)
        trigger = evaluate_trigger(rain, aqi)
        return TriggerCheckResponse(rain=rain, aqi=aqi, trigger=TriggerDecision(**trigger))
    except Exception:
        return TriggerCheckResponse(rain=0.0, aqi=0.0, trigger=TriggerDecision(trigger=False))