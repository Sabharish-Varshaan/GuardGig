from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/api/trigger", tags=["trigger"])

class TriggerCheckRequest(BaseModel):
    location: str

class TriggerCheckResponse(BaseModel):
    trigger: str

async def get_weather_rain(location: str) -> float:
    """Fetch current rain amount from weather API."""
    url = f"https://wttr.in/{location}?format=j1"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            rain = float(data['current_condition'][0]['precipMM'])
            return rain
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Weather API error: {str(e)}")

@router.post("/check", response_model=TriggerCheckResponse)
async def check_trigger(request: TriggerCheckRequest):
    try:
        rain = await get_weather_rain(request.location)
        trigger = "none"
        if rain >= 100:
            trigger = "full"
        elif rain >= 60:
            trigger = "partial"
        return TriggerCheckResponse(trigger=trigger)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))