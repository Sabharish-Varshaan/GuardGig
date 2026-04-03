from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..dependencies import require_current_user
from ..premium_utils import calculate_premium
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
        return "ineligible", "low", 0

    active_days = max(0, (datetime.now(timezone.utc) - created_at).days)

    if active_days < 5:
        return "ineligible", "low", active_days

    if 5 <= active_days < 7:
        return "eligible", "low", active_days

    return "eligible", "medium", active_days

@router.post("/create", response_model=PolicyCreateResponse)
def create_policy(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    # Check if user has completed onboarding
    onboarding_response = (
        admin.table(settings.supabase_onboarding_table)
        .select("mean_income, income_variance, min_income, max_income, daily_income, risk_preference, onboarding_completed, created_at")
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
    if mean_income is None and onboarding.get("daily_income") is not None:
        mean_income = float(onboarding["daily_income"])

    if mean_income is None or float(mean_income) <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid onboarding income model. Please resubmit onboarding details."
        )

    mean_income = float(mean_income)
    income_variance = float(onboarding.get("income_variance") or 0)
    weekly_income = int(round(mean_income * 7))
    risk_preference = onboarding.get("risk_preference", "Medium")
    eligibility_status, worker_tier, active_days = _derive_underwriting(onboarding.get("created_at"))

    if eligibility_status == "ineligible":
        return PolicyCreateResponse(
            status="ineligible",
            policy=None,
            message="User is ineligible for policy creation based on onboarding age.",
        )

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

    # Calculate premium
    premium = calculate_premium(float(weekly_income), str(risk_preference), income_variance=income_variance)

    # Create policy
    now = datetime.now(timezone.utc)
    policy_data = {
        "user_id": current_user["id"],
        "weekly_income": weekly_income,
        "min_income": float(onboarding.get("min_income") or round(mean_income * 0.7, 2)),
        "max_income": float(onboarding.get("max_income") or round(mean_income * 1.3, 2)),
        "mean_income": round(mean_income, 2),
        "income_variance": round(income_variance, 4),
        "premium": premium,
        "coverage_amount": 700.00,
        "policy_start_date": now.date().isoformat(),
        "status": "active",
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

    policy = rows[0]
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

    policy = rows[0]
    return PolicyResponse(**policy)