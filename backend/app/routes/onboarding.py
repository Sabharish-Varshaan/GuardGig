from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import OnboardingRequest, OnboardingResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


def _compute_variance(min_income: float, max_income: float, mean_income: float) -> float:
    if mean_income == 0:
        return 0.0
    return (max_income - min_income) / mean_income


def _normalize_profile(profile: dict) -> dict:
    normalized = dict(profile)
    daily_income = normalized.get("daily_income")

    min_income = normalized.get("min_income")
    max_income = normalized.get("max_income")
    mean_income = normalized.get("mean_income")
    income_variance = normalized.get("income_variance")

    if min_income is None and daily_income is not None:
        min_income = round(float(daily_income) * 0.7, 2)

    if max_income is None and daily_income is not None:
        max_income = round(float(daily_income) * 1.3, 2)

    if mean_income is None:
        if daily_income is not None:
            mean_income = float(daily_income)
        elif min_income is not None and max_income is not None:
            mean_income = (float(min_income) + float(max_income)) / 2

    if income_variance is None and min_income is not None and max_income is not None and mean_income is not None:
        income_variance = _compute_variance(float(min_income), float(max_income), float(mean_income))

    normalized["min_income"] = min_income
    normalized["max_income"] = max_income
    normalized["mean_income"] = mean_income
    normalized["income_variance"] = income_variance if income_variance is not None else 0.0

    return normalized


@router.get("/me", response_model=OnboardingResponse)
def get_my_onboarding_profile(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    try:
        response = (
            admin.table(settings.supabase_onboarding_table)
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch onboarding profile"
        ) from exc

    rows = response.data or []
    if not rows:
        return OnboardingResponse(onboarding_completed=False, profile={})

    profile = _normalize_profile(rows[0])
    return OnboardingResponse(
        onboarding_completed=bool(profile.get("onboarding_completed", False)),
        profile=profile
    )


@router.post("", response_model=OnboardingResponse)
def submit_onboarding(
    payload: OnboardingRequest,
    current_user: dict = Depends(require_current_user)
):
    settings = get_settings()
    admin = get_admin_client()

    min_income = float(payload.min_income)
    max_income = float(payload.max_income)
    mean_income = (min_income + max_income) / 2
    income_variance = _compute_variance(min_income, max_income, mean_income)
    # Keep legacy columns populated for transition safety.
    daily_income = int(round(mean_income))
    weekly_income = int(round(mean_income * 7))

    onboarding_row = {
        "user_id": current_user["id"],
        "full_name": payload.full_name,
        "age": payload.age,
        "city": payload.city,
        "platform": payload.platform,
        "vehicle_type": payload.vehicle_type,
        "work_hours": payload.work_hours,
        "daily_income": daily_income,
        "weekly_income": weekly_income,
        "min_income": round(min_income, 2),
        "max_income": round(max_income, 2),
        "mean_income": round(mean_income, 2),
        "income_variance": round(income_variance, 4),
        "risk_preference": payload.risk_preference,
        "onboarding_completed": True,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        response = (
            admin.table(settings.supabase_onboarding_table)
            .upsert(onboarding_row, on_conflict="user_id")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to save onboarding profile"
        ) from exc

    rows = response.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Onboarding save completed but no profile returned"
        )

    return OnboardingResponse(onboarding_completed=True, profile=_normalize_profile(rows[0]))
