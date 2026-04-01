from fastapi import APIRouter, Depends, HTTPException, status

from ..claim_rules import (
    calculate_fraud_score,
    enforce_exclusions,
    enforce_max_one_claim_per_day,
    enforce_waiting_period,
    fetch_recent_claim_count,
)
from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import ClaimCreateRequest, ClaimCreateResponse, ClaimsListResponse, ClaimResponse
from ..supabase_client import get_admin_client
from ..trigger_utils import evaluate_rain_trigger, fetch_aqi, fetch_rain_mm

router = APIRouter(prefix="/api", tags=["claim"])

def calculate_payout(trigger: str, coverage_amount: float) -> float:
    if trigger == "full":
        return round(coverage_amount, 2)
    if trigger == "partial":
        return round(coverage_amount * 0.30, 2)
    return 0.0

@router.post("/claim/create", response_model=ClaimCreateResponse)
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
    coverage_amount = float(policy.get("coverage_amount", 700.0))

    try:
        enforce_waiting_period(policy, waiting_hours=24)
        enforce_max_one_claim_per_day(admin, settings.supabase_claims_table, current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    rain = await fetch_rain_mm(request.location)
    _aqi = await fetch_aqi(request.location)
    trigger = evaluate_rain_trigger(rain)

    if trigger == "none":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No claim trigger conditions met")

    recent_claim_count = fetch_recent_claim_count(admin, settings.supabase_claims_table, current_user["id"])
    effective_location_valid = bool(request.location.strip()) and request.location_valid
    fraud_score = calculate_fraud_score(
        activity_status=request.activity_status,
        location_valid=effective_location_valid,
        claim_frequency=recent_claim_count,
    )

    try:
        enforce_exclusions(
            activity_status=request.activity_status,
            location_valid=effective_location_valid,
            fraud_score=fraud_score,
            fraud_threshold=settings.claim_fraud_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    payout = calculate_payout(trigger, coverage_amount)

    # Create claim
    claim_data = {
        "user_id": current_user["id"],
        "policy_id": policy["id"],
        "trigger_type": "rain",
        "trigger_value": rain,
        "payout_amount": payout,
        "status": "approved",
        "fraud_score": fraud_score,
        "activity_status": request.activity_status,
        "location_valid": effective_location_valid,
        "rule_decision_reason": "approved_after_rule_checks",
    }

    claim_response = admin.table(settings.supabase_claims_table).insert(claim_data).execute()

    if not claim_response.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create claim")

    claim = claim_response.data[0]

    return ClaimCreateResponse(
        claim=ClaimResponse(**claim),
        message="Claim created successfully"
    )

@router.get("/claims/me", response_model=ClaimsListResponse)
def get_my_claims(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    claims_response = (
        admin.table(settings.supabase_claims_table)
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
    )

    claims = [ClaimResponse(**claim) for claim in (claims_response.data or [])]

    return ClaimsListResponse(claims=claims)