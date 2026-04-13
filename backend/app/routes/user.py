from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..dependencies import require_current_user
from ..payout_utils import mask_bank_account
from ..schemas import DemoModeToggleRequest, DemoModeToggleResponse, PayoutDetailsCreateRequest, PayoutDetailsResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/user", tags=["user"])


def _map_payout_details_response(row: dict, message: str) -> PayoutDetailsResponse:
    return PayoutDetailsResponse(
        account_holder_name=row.get("account_holder_name", ""),
        bank_account_number_masked=mask_bank_account(row.get("bank_account_number")),
        ifsc_code=row.get("ifsc_code"),
        upi_id=row.get("upi_id"),
        created_at=row.get("created_at"),
        message=message,
    )


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


@router.post("/payout-details", response_model=PayoutDetailsResponse)
def set_payout_details(payload: PayoutDetailsCreateRequest, current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    existing_response = (
        admin.table(settings.supabase_payout_details_table)
        .select("id")
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    existing_rows = existing_response.data or []

    data = {
        "user_id": current_user["id"],
        "account_holder_name": payload.account_holder_name,
        "bank_account_number": payload.bank_account_number,
        "ifsc_code": payload.ifsc_code,
        "upi_id": payload.upi_id,
    }

    if existing_rows:
        response = (
            admin.table(settings.supabase_payout_details_table)
            .update(data)
            .eq("user_id", current_user["id"])
            .execute()
        )
        message = "Payout details updated"
    else:
        response = admin.table(settings.supabase_payout_details_table).insert(data).execute()
        message = "Payout details saved"

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save payout details")

    return _map_payout_details_response(rows[0], message)


@router.get("/payout-details", response_model=PayoutDetailsResponse)
def get_payout_details(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    response = (
        admin.table(settings.supabase_payout_details_table)
        .select("account_holder_name,bank_account_number,ifsc_code,upi_id,created_at")
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )

    rows = response.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please add payout details to receive compensation",
        )

    return _map_payout_details_response(rows[0], "Payout details available")
