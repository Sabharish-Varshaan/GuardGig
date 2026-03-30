from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import OnboardingRequest, OnboardingResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


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

    profile = rows[0]
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

    onboarding_row = {
        "user_id": current_user["id"],
        "full_name": payload.full_name,
        "age": payload.age,
        "city": payload.city,
        "platform": payload.platform,
        "vehicle_type": payload.vehicle_type,
        "work_hours": payload.work_hours,
        "daily_income": payload.daily_income,
        "weekly_income": payload.weekly_income,
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

    return OnboardingResponse(onboarding_completed=True, profile=rows[0])
