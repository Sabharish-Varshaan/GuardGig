from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import (
    get_settings,
    LOSS_RATIO_THRESHOLD,
    LOSS_RATIO_MIN_PREMIUM_FOR_ENFORCEMENT,
)
from ..dependencies import require_current_user
from ..metrics_utils import check_loss_ratio_threshold
from ..premium_utils import calculate_policy_risk_score, calculate_premium
from ..services.policy_lifecycle_service import update_policy_status
from ..schemas import PolicyCreateResponse, PolicyResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/policy", tags=["policy"])


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _derive_underwriting(onboarding_created_at: str | None) -> tuple[str, str, int]:
    created_at = _parse_datetime(onboarding_created_at)
    if created_at is None:
        return "eligible", "low", 0

    active_days = max(0, (datetime.now(timezone.utc) - created_at).days)

    if active_days < 7:
        return "eligible", "low", active_days

    return "eligible", "medium", active_days

@router.post("/create", response_model=PolicyCreateResponse)
def create_policy(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    # Check loss ratio threshold - block policy creation if risk is too high
    try:
        check_loss_ratio_threshold(
            admin,
            threshold=LOSS_RATIO_THRESHOLD,
            min_total_premium_for_enforcement=LOSS_RATIO_MIN_PREMIUM_FOR_ENFORCEMENT,
        )
    except ValueError as exc:
        return PolicyCreateResponse(
            status="ineligible",
            policy=None,
            message=str(exc),
        )

    # Check if user has completed onboarding
    onboarding_response = (
        admin.table(settings.supabase_onboarding_table)
        .select("mean_income, income_variance, min_income, max_income, risk_preference, onboarding_completed, created_at")
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )

    onboarding_rows = onboarding_response.data or []
    if not onboarding_rows:
        return PolicyCreateResponse(
            status="ineligible",
            policy=None,
            message="Onboarding not completed. Please complete onboarding first.",
        )

    onboarding = onboarding_rows[0]
    if not onboarding.get("onboarding_completed", False):
        return PolicyCreateResponse(
            status="ineligible",
            policy=None,
            message="Onboarding not completed. Please complete onboarding first.",
        )

    mean_income = onboarding.get("mean_income")
    min_income = onboarding.get("min_income")
    max_income = onboarding.get("max_income")

    if mean_income is None or float(mean_income) <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid onboarding income model. Please resubmit onboarding details."
        )

    if min_income is None or max_income is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incomplete onboarding income range. Please resubmit onboarding details."
        )

    min_income = float(min_income)
    max_income = float(max_income)
    if min_income <= 0 or max_income <= min_income:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid onboarding income range. Please resubmit onboarding details."
        )

    mean_income = float(mean_income)
    income_variance = float(onboarding.get("income_variance") or 0)
    weekly_income = int(round(mean_income * 7))
    risk_preference = onboarding.get("risk_preference", "Medium")
    eligibility_status, worker_tier, active_days = _derive_underwriting(onboarding.get("created_at"))

    if settings.demo_mode:
        eligibility_status = "eligible"
        worker_tier = "medium"

    # Check if policy already exists
    existing_policy = (
        admin.table(settings.supabase_policies_table)
        .select("id")
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )

    if existing_policy.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Policy already exists for this user"
        )

    # Evaluate policy risk once and reuse in pricing + underwriting decisions.
    risk_score = calculate_policy_risk_score(float(weekly_income), income_variance=income_variance)

    # Calculate premium
    premium = calculate_premium(float(mean_income), str(risk_preference), income_variance=income_variance)

    coverage_amount = 700.00
    if risk_score > 0.7:
        coverage_amount = round(coverage_amount * 0.8, 2)

    # Create policy
    now = datetime.now(timezone.utc)
    end_date = (now + timedelta(days=7)).isoformat()
    policy_data = {
        "user_id": current_user["id"],
        "weekly_income": weekly_income,
        "min_income": round(min_income, 2),
        "max_income": round(max_income, 2),
        "mean_income": round(mean_income, 2),
        "income_variance": round(income_variance, 4),
        "risk_score": round(risk_score, 4),
        "premium": premium,
        "coverage_amount": coverage_amount,
        "policy_start_date": now.date().isoformat(),
        "end_date": end_date,
        "status": "inactive",
        "payment_status": "pending",
        "eligibility_status": eligibility_status,
        "worker_tier": worker_tier,
        "active_days": active_days,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }

    try:
        response = (
            admin.table(settings.supabase_policies_table)
            .insert(policy_data)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create policy: {str(exc)}"
        ) from exc

    rows = response.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy creation completed but no policy returned"
        )

    policy = update_policy_status(admin, settings.supabase_policies_table, rows[0])
    return PolicyCreateResponse(
        status="created",
        policy=PolicyResponse(**policy),
        message="Policy created successfully"
    )


@router.get("/me", response_model=PolicyResponse)
def get_my_policy(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    try:
        response = (
            admin.table(settings.supabase_policies_table)
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch policy"
        ) from exc

    rows = response.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No policy found for this user"
        )

    policy = update_policy_status(admin, settings.supabase_policies_table, rows[0])
    return PolicyResponse(**policy)