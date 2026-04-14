from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from ..trigger_utils import check_trigger as evaluate_trigger, fetch_trigger_snapshot

router = APIRouter(prefix="/api/trigger", tags=["trigger"])

class TriggerCheckRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    location: str | None = None
    lat: float | None = None
    lon: float | None = None


class TriggerCheckResponse(BaseModel):
    rain: float
    aqi: float
    temperature: float
    triggered: bool
    trigger_type: str | None = None
    severity: str | None = None
    payout_percentage: int | None = None
    trigger_value: float | None = None
    trigger_reason: str | None = None
    heat_percentage: int | None = None

@router.post("/check", response_model=TriggerCheckResponse)
async def check_trigger(request: TriggerCheckRequest):
    try:
        rain, aqi, temperature = await fetch_trigger_snapshot(request.location, request.lat, request.lon)
        trigger = evaluate_trigger(rain, aqi, temperature)
        return TriggerCheckResponse(
            rain=rain,
            aqi=aqi,
            temperature=temperature,
            triggered=trigger.get("triggered", False),
            trigger_type=trigger.get("trigger_type"),
            severity=trigger.get("severity"),
            payout_percentage=trigger.get("payout_percentage"),
            trigger_value=trigger.get("trigger_value"),
            trigger_reason=trigger.get("trigger_reason"),
            heat_percentage=trigger.get("heat_percentage"),
        )
    except Exception:
        return TriggerCheckResponse(
            rain=0.0,
            aqi=0.0,
            temperature=0.0,
            triggered=False,
            trigger_type=None,
            severity=None,
            payout_percentage=None,
            trigger_value=None,
            trigger_reason=None,
            heat_percentage=None,
        )
