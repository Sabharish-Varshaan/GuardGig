from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone
from uuid import uuid4

from ..auth_utils import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password
)
from ..config import get_settings
from ..schemas import AuthResponse, LoginRequest, RegisterRequest
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _get_onboarding_status(user_id: str) -> bool:
    settings = get_settings()
    admin = get_admin_client()

    response = (
        admin.table(settings.supabase_onboarding_table)
        .select("onboarding_completed")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    rows = response.data or []
    if not rows:
        return False

    return bool(rows[0].get("onboarding_completed", False))


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    settings = get_settings()
    admin = get_admin_client()
    metadata = {
        "full_name": payload.full_name
    }

    existing = (
        admin.table(settings.supabase_users_table)
        .select("id")
        .eq("phone", payload.phone)
        .limit(1)
        .execute()
    )

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered"
        )

    user_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    try:
        admin.table(settings.supabase_users_table).insert(
            {
                "id": user_id,
                "full_name": metadata["full_name"],
                "phone": payload.phone,
                "password_hash": hash_password(payload.password),
                "created_at": now,
                "updated_at": now
            }
        ).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to register user: {str(exc)}"
        ) from exc

    access_token = create_access_token(user_id=user_id, phone=payload.phone)
    refresh_token = create_refresh_token(user_id=user_id, phone=payload.phone)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        onboarding_completed=False
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    settings = get_settings()
    admin = get_admin_client()

    result = (
        admin.table(settings.supabase_users_table)
        .select("id,phone,password_hash")
        .eq("phone", payload.phone)
        .limit(1)
        .execute()
    )

    rows = result.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or password"
        )

    user = rows[0]

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or password"
        )

    onboarding_completed = _get_onboarding_status(user["id"])
    access_token = create_access_token(user_id=user["id"], phone=user["phone"])
    refresh_token = create_refresh_token(user_id=user["id"], phone=user["phone"])

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user["id"],
        onboarding_completed=onboarding_completed
    )
