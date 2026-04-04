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
from ..schemas import ClaimCreateRequest, ClaimCreateResponse, ClaimRejectedResponse, ClaimsListResponse, ClaimResponse
from ..supabase_client import get_admin_client
from ..trigger_utils import check_trigger, fetch_aqi, fetch_rain_mm

router = APIRouter(prefix="/api", tags=["claim"])


def _coordinates_are_valid(lat: float | None, lon: float | None) -> bool:
    if lat is None or lon is None:
        return False

    return -90.0 <= float(lat) <= 90.0 and -180.0 <= float(lon) <= 180.0

def calculate_payout(severity: str, base_amount: float, coverage_amount: float) -> float:
    capped_base = min(base_amount, coverage_amount)

    if severity == "full":
        return round(min(capped_base, coverage_amount), 2)
    if severity == "partial":
        return round(min(capped_base * 0.30, coverage_amount), 2)
    return 0.0

@router.post("/claim/create", response_model=ClaimCreateResponse | ClaimRejectedResponse)
async def create_claim(request: ClaimCreateRequest, current_user: dict = Depends(require_current_user)) -> ClaimCreateResponse | ClaimRejectedResponse:
    settings = get_settings()
    admin = get_admin_client()

    if not _coordinates_are_valid(request.lat, request.lon):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid lat/lon coordinates are required"
        )

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

    onboarding_response = (
        admin.table(settings.supabase_onboarding_table)
        .select("mean_income")
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )

    onboarding_rows = onboarding_response.data or []
    onboarding_profile = onboarding_rows[0] if onboarding_rows else {}
    mean_income = onboarding_profile.get("mean_income")

    if mean_income is None or float(mean_income) <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid onboarding income model. Please resubmit onboarding details."
        )

    payout_base = min(float(mean_income), coverage_amount)

    try:
        enforce_max_one_claim_per_day(admin, settings.supabase_claims_table, current_user["id"])
    except ValueError:
        return ClaimRejectedResponse(status="rejected", reason="Daily claim limit reached")

    if not settings.demo_mode:
        try:
            enforce_waiting_period(policy, waiting_hours=24)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    rain = await fetch_rain_mm(None, request.lat, request.lon)
    aqi = await fetch_aqi(None, request.lat, request.lon)
    trigger_data = check_trigger(rain, aqi)

    if not trigger_data.get("trigger"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No claim trigger conditions met")

    trigger_type = trigger_data["type"]
    severity = trigger_data["severity"]

    recent_claim_count = 0 if settings.demo_mode else fetch_recent_claim_count(admin, settings.supabase_claims_table, current_user["id"])
    effective_location_valid = _coordinates_are_valid(request.lat, request.lon)
    fraud_score = calculate_fraud_score(
        activity_status=request.activity_status,
        location_valid=effective_location_valid,
        claim_frequency=recent_claim_count,
    )

    if not settings.demo_mode:
        try:
            enforce_exclusions(
                activity_status=request.activity_status,
                location_valid=effective_location_valid,
                fraud_score=fraud_score,
                fraud_threshold=settings.claim_fraud_threshold,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    payout = calculate_payout(severity, payout_base, coverage_amount)

    trigger_value = rain if trigger_type == "rain" else aqi

    # Create claim
    claim_data = {
        "user_id": current_user["id"],
        "policy_id": policy["id"],
        "trigger_type": trigger_type,
        "trigger_value": trigger_value,
        "payout_amount": payout,
        "status": "approved",
        "fraud_score": fraud_score,
        "activity_status": request.activity_status,
        "location_valid": effective_location_valid,
        "rule_decision_reason": f"approved_after_{trigger_type}_{severity}_checks",
    }

    try:
        claim_response = admin.table(settings.supabase_claims_table).insert(claim_data).execute()
    except Exception as exc:
        if "daily claim limit reached" in str(exc).lower():
            return ClaimRejectedResponse(status="rejected", reason="Daily claim limit reached")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create claim") from exc

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