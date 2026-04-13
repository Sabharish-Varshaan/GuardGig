from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import DemoModeToggleRequest, DemoModeToggleResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/settings/demo-mode", response_model=DemoModeToggleResponse)
def get_demo_mode_setting(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    response = (
        admin.table(settings.supabase_users_table)
        .select("demo_mode_enabled,demo_mode_enabled_at")
        .eq("id", current_user["id"])
        .limit(1)
        .execute()
    )

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    row = rows[0]
    enabled = bool(row.get("demo_mode_enabled", False))
    return DemoModeToggleResponse(
        demo_mode_enabled=enabled,
        updated_at=row.get("demo_mode_enabled_at"),
        message="Demo mode is enabled" if enabled else "Demo mode is disabled",
    )


@router.post("/settings/demo-mode", response_model=DemoModeToggleResponse)
def set_demo_mode_setting(payload: DemoModeToggleRequest, current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    now_iso = datetime.now(timezone.utc).isoformat()
    response = (
        admin.table(settings.supabase_users_table)
        .update(
            {
                "demo_mode_enabled": payload.enabled,
                "demo_mode_enabled_at": now_iso if payload.enabled else None,
                "updated_at": now_iso,
            }
        )
        .eq("id", current_user["id"])
        .execute()
    )

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    row = rows[0]
    enabled = bool(row.get("demo_mode_enabled", False))
    return DemoModeToggleResponse(
        demo_mode_enabled=enabled,
        updated_at=row.get("demo_mode_enabled_at"),
        message="Demo mode enabled" if enabled else "Demo mode disabled",
    )
