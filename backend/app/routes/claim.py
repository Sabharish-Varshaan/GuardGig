from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx

from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import ClaimCreateRequest, ClaimCreateResponse, ClaimsListResponse, ClaimResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/claim", tags=["claim"])

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

def calculate_payout(trigger: str) -> float:
    """Calculate payout based on trigger."""
    if trigger == "full":
        return 700.0
    elif trigger == "partial":
        return 0.3 * 700.0
    else:
        return 0.0

@router.post("/create", response_model=ClaimCreateResponse)
async def create_claim(request: ClaimCreateRequest, current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    # Get user's active policy
    policy_response = (
        admin.table(settings.supabase_policies_table)
        .select("*")
        .eq("user_id", current_user["id"])
        .eq("status", "active")
        .limit(1)
        .execute()
    )

    if not policy_response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active policy found")

    policy = policy_response.data[0]

    # Get weather data
    rain = await get_weather_rain(request.location)

    # Determine trigger
    trigger = "none"
    if rain >= 100:
        trigger = "full"
    elif rain >= 60:
        trigger = "partial"

    if trigger == "none":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No claim trigger conditions met")

    payout = calculate_payout(trigger)

    # Create claim
    claim_data = {
        "user_id": current_user["id"],
        "policy_id": policy["id"],
        "trigger_type": "rain",
        "trigger_value": rain,
        "payout_amount": payout,
        "status": "approved",  # Simplified: auto-approve if conditions met
        "fraud_score": 0.0  # Placeholder
    }

    claim_response = admin.table("claims").insert(claim_data).execute()

    if not claim_response.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create claim")

    claim = claim_response.data[0]

    return ClaimCreateResponse(
        claim=ClaimResponse(**claim),
        message="Claim created successfully"
    )

@router.get("/me", response_model=ClaimsListResponse)
def get_my_claims(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    claims_response = (
        admin.table("claims")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
    )

    claims = [ClaimResponse(**claim) for claim in claims_response.data]

    return ClaimsListResponse(claims=claims)