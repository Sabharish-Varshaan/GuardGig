from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import PolicyCreateResponse, PolicyResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/policy", tags=["policy"])


def _calculate_premium(weekly_income: int) -> float:
    """Calculate premium as 5% of weekly income."""
    return round(weekly_income * 0.05, 2)


@router.post("/create", response_model=PolicyCreateResponse)
def create_policy(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    # Check if user has completed onboarding
    onboarding_response = (
        admin.table(settings.supabase_onboarding_table)
        .select("weekly_income, onboarding_completed")
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )

    onboarding_rows = onboarding_response.data or []
    if not onboarding_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding not completed. Please complete onboarding first."
        )

    onboarding = onboarding_rows[0]
    if not onboarding.get("onboarding_completed", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding not completed. Please complete onboarding first."
        )

    weekly_income = onboarding["weekly_income"]

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
    premium = _calculate_premium(weekly_income)

    # Create policy
    now = datetime.now(timezone.utc)
    policy_data = {
        "user_id": current_user["id"],
        "weekly_income": weekly_income,
        "premium": premium,
        "coverage_amount": 700.00,
        "policy_start_date": now.date().isoformat(),
        "status": "active",
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