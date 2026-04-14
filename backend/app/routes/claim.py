from datetime import datetime, timezone

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
from ..services.payout_details_service import fetch_user_payout_details, resolve_claim_payout_destination
from ..services.payment_service import persist_claim_payment, simulate_razorpay_payout
from ..supabase_client import get_admin_client
from ..trigger_utils import check_trigger

router = APIRouter(prefix="/api", tags=["claim"])


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

    policy = policy_rows[0]
    expires_at = _parse_iso_datetime(policy.get("expires_at"))
    if expires_at is None or datetime.now(timezone.utc) > expires_at:
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
    severity = trigger_data["severity"]
    payout_percentage_raw = trigger_data["payout_percentage"]
    trigger_value = trigger_data["trigger_value"]
    trigger_reason = trigger_data["trigger_reason"]

    coverage_amount = float(policy.get("coverage_amount", 700.0))
    payout_base = min(mean_income, coverage_amount)
    payout = round((payout_percentage_raw / 100.0) * payout_base, 2)
    payout = max(0.0, min(payout, coverage_amount))

    claim_count = fetch_recent_claim_count(admin, settings.supabase_claims_table, current_user["id"])
    fraud_score = calculate_fraud_score(
        activity_status="active",
        location_valid=True,
        claim_frequency=claim_count,
    )
    try:
        enforce_exclusions(
            activity_status="active",
            location_valid=True,
            fraud_score=fraud_score,
            fraud_threshold=settings.claim_fraud_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    now_iso = datetime.now(timezone.utc).isoformat()
    rule_decision_reason = f"demo_mode_{trigger_type}_{severity}_manual"
    trigger_snapshot = {
        "trigger_type": trigger_type,
        "severity": severity,
        "rain": 120.0,
        "aqi": 50.0,
        "temperature": 45.0,
        "heat_percentage": trigger_data.get("heat_percentage", 0),
        "payout_percentage": payout_percentage_raw,
        "payout_amount": payout,
        "fraud_score": fraud_score,
        "activity_status": "active",
        "location_valid": True,
        "rule_decision_reason": rule_decision_reason,
        "trigger_reason": trigger_reason,
        "city": city,
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
        "fraud_score": fraud_score,
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

    payout_details = fetch_user_payout_details(admin, settings.supabase_payout_details_table, current_user["id"])
    payout_destination = resolve_claim_payout_destination(payout_details)
    payout_method = "pending"
    masked_account = None

    if not payout_destination:
        payment_status = "pending_payout_details"
        transaction_id = None
        paid_at = None
    else:
        payout_method, masked_account = payout_destination
        try:
            payout_result = simulate_razorpay_payout(payout, current_user["id"])
            payment_status = payout_result["status"]
            transaction_id = payout_result["transaction_id"]
            paid_at = payout_result["paid_at"]
        except Exception:
            payment_status = "failed"
            transaction_id = None
            paid_at = None

    persist_claim_payment(
        admin,
        settings.supabase_claims_table,
        claim["id"],
        payment_status,
        transaction_id,
        paid_at,
        payout_method,
        masked_account,
        trigger_snapshot,
    )

    latest_notification = None
    if claim.get("status") == "approved" and payment_status in {"paid", "credited"} and payout > 0:
        update_metrics_on_payout(admin, payout)

        latest_notification = create_notification(
            admin,
            settings.supabase_notifications_table,
            user_id=current_user["id"],
            title="Payout Credited 💸",
            message=f"₹{payout:.2f} credited due to {trigger_type}",
            notification_type="payout_credited",
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