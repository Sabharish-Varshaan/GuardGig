from datetime import datetime, timezone
import logging

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
from ..metrics_utils import update_metrics_on_payout
from ..schemas import ClaimCreateResponse, ClaimsListResponse, ClaimResponse
from ..services.notification_service import create_notification
from ..services.policy_lifecycle_service import update_policy_status
from ..services.payout_service import process_payout
from ..supabase_client import get_admin_client
from ..trigger_utils import TRIGGERS, check_trigger

router = APIRouter(prefix="/api", tags=["claim"])
logger = logging.getLogger(__name__)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


@router.post("/claims/demo", response_model=ClaimCreateResponse)
def create_demo_claim(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    if not bool(current_user.get("demo_mode_enabled", False)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enable demo mode first before creating a demo claim.",
        )

    policy_response = (
        admin.table(settings.supabase_policies_table)
        .select("*")
        .eq("user_id", current_user["id"])
        .eq("status", "active")
        .eq("payment_status", "success")
        .limit(1)
        .execute()
    )
    policy_rows = policy_response.data or []
    if not policy_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active paid policy found. Complete payment to activate policy first.",
        )

    policy = update_policy_status(admin, settings.supabase_policies_table, policy_rows[0])
    expires_at = _parse_iso_datetime(policy.get("end_date") or policy.get("expires_at"))
    if str(policy.get("status") or "").lower() != "active" or expires_at is None or datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy expired or invalid expiry. Renew policy first.",
        )

    onboarding_response = (
        admin.table(settings.supabase_onboarding_table)
        .select("city,mean_income")
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    onboarding_rows = onboarding_response.data or []
    onboarding = onboarding_rows[0] if onboarding_rows else {}
    city = onboarding.get("city")
    mean_income = float(onboarding.get("mean_income") or 0)
    if not city or mean_income <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding profile is incomplete for demo claim creation.",
        )

    try:
        enforce_max_one_claim_per_day(admin, settings.supabase_claims_table, current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        enforce_waiting_period(policy, waiting_hours=24)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    trigger_data = check_trigger(120.0, 50.0, 45.0)
    if not trigger_data.get("triggered"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Demo trigger failed")

    trigger_type = trigger_data["trigger_type"]
    if trigger_type not in TRIGGERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trigger type")
    severity = trigger_data["severity"]
    payout_percentage_raw = trigger_data["payout_percentage"]
    trigger_value = trigger_data["trigger_value"]
    trigger_reason = trigger_data["trigger_reason"]

    coverage_amount = float(policy.get("coverage_amount", 700.0))
    risk_score = float(policy.get("risk_score") or 0.0)
    payout_base = min(mean_income, coverage_amount)
    payout = round((payout_percentage_raw / 100.0) * payout_base, 2)
    payout = max(0.0, min(payout, coverage_amount))

    claim_count = fetch_recent_claim_count(admin, settings.supabase_claims_table, current_user["id"])
    fraud_score = calculate_fraud_score(
        activity_status="active",
        location_valid=True,
        claim_frequency=claim_count,
        location_change_km=0.0,
        reported_rain_mm=120.0,
        actual_rain_mm=120.0,
    )
    original_payout_percentage = payout_percentage_raw
    try:
        enforce_exclusions(
            activity_status="active",
            location_valid=True,
            fraud_score=fraud_score,
            fraud_threshold=settings.claim_fraud_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if fraud_score > 0.6:
        payout_percentage_raw = int(round(payout_percentage_raw * 0.5))
        payout = round((payout_percentage_raw / 100.0) * payout_base, 2)
        payout = max(0.0, min(payout, coverage_amount))

    decision_reason = f"demo_mode_{trigger_type}_{severity}_manual"
    if fraud_score > 0.6:
        decision_reason = f"{decision_reason}_medium_fraud_adjusted"

    logger.info(
        "ML decision finalized: fraud_score=%.2f, risk_score=%.2f, payout=%.2f, payout_percentage=%s%%",
        fraud_score,
        risk_score,
        payout,
        payout_percentage_raw,
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    rule_decision_reason = decision_reason
    trigger_snapshot = {
        "trigger_type": trigger_type,
        "severity": severity,
        "rain": 120.0,
        "aqi": 50.0,
        "temperature": 45.0,
        "location_change_km": 0.0,
        "reported_rain_mm": 120.0,
        "actual_rain_mm": 120.0,
        "heat_percentage": trigger_data.get("heat_percentage", 0),
        "payout_percentage": payout_percentage_raw,
        "payout_amount": payout,
        "fraud_score": fraud_score,
        "risk_score": risk_score,
        "activity_status": "active",
        "location_valid": True,
        "rule_decision_reason": rule_decision_reason,
        "trigger_reason": trigger_reason,
        "city": city,
        "original_payout_percentage": original_payout_percentage,
    }

    claim_data = {
        "user_id": current_user["id"],
        "policy_id": policy["id"],
        "trigger_type": trigger_type,
        "trigger_value": trigger_value,
        "trigger_reason": trigger_reason,
        "payout_percentage": payout_percentage_raw,
        "payout_amount": payout,
        "status": "approved",
        "payout_status": "pending",
        "fraud_score": fraud_score,
        "risk_score": risk_score,
        "activity_status": "active",
        "location_valid": True,
        "rule_decision_reason": rule_decision_reason,
        "updated_at": now_iso,
    }

    try:
        claim_response = admin.table(settings.supabase_claims_table).insert(claim_data).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create demo claim: {str(exc)}",
        ) from exc

    claim_rows = claim_response.data or []
    if not claim_rows:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Demo claim insert returned no rows")

    claim = claim_rows[0]

    payout_result = process_payout(
        claim,
        admin=admin,
        claims_table=settings.supabase_claims_table,
        payout_details_table=settings.supabase_payout_details_table,
        trigger_snapshot=trigger_snapshot,
    )
    payment_status = payout_result["payment_status"]
    payout_method = payout_result["payout_method"]
    transaction_id = payout_result["transaction_id"]

    latest_notification = None
    if claim.get("status") == "approved" and payment_status in {"paid", "credited"} and payout > 0:
        update_metrics_on_payout(admin, payout)

        latest_notification = create_notification(
            admin,
            settings.supabase_notifications_table,
            user_id=current_user["id"],
            title="Payout Credited 💰",
            message=f"₹{payout:.2f} has been credited via {str(payout_method).upper()}",
            notification_type="payout",
            claim_id=claim["id"],
            metadata={
                "trigger_type": trigger_type,
                "trigger_reason": trigger_reason,
                "payout_amount": payout,
                "transaction_id": transaction_id,
            },
        )

    refreshed_claim_response = (
        admin.table(settings.supabase_claims_table)
        .select("*")
        .eq("id", claim["id"])
        .limit(1)
        .execute()
    )
    refreshed_rows = refreshed_claim_response.data or []
    if not refreshed_rows:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Demo claim created but reload failed")

    return ClaimCreateResponse(
        claim=ClaimResponse(**refreshed_rows[0]),
        message="Demo claim created and payout processed",
        notification=latest_notification,
    )