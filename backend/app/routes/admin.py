"""
Admin endpoints for system metrics and risk oversight.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth_utils import create_access_token, verify_password
from ..config import get_settings
from ..dependencies import require_admin_user
from ..metrics_utils import get_full_metrics
from ..schemas import AdminLoginRequest, AdminLoginResponse, AdminMetricsResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest):
    settings = get_settings()
    admin = get_admin_client()

    result = (
        admin.table(settings.supabase_users_table)
        .select("id,full_name,email,phone,password_hash,role")
        .eq("email", payload.email)
        .limit(1)
        .execute()
    )

    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    user = rows[0]
    if user.get("role", "user") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    access_token = create_access_token(
        user_id=user["id"],
        phone=user.get("phone", ""),
        role="admin",
        email=user.get("email")
    )

    return AdminLoginResponse(access_token=access_token, role="admin")


@router.get("/metrics", response_model=AdminMetricsResponse)
def get_metrics(current_admin: dict = Depends(require_admin_user)):
    """
    Fetch system metrics: total premiums, payouts, and loss ratio.
    Used for admin dashboard and risk control oversight.
    """
    admin = get_admin_client()
    metrics = get_full_metrics(admin)
    
    # Determine health status based on loss ratio
    loss_ratio = metrics["loss_ratio"]
    if loss_ratio < 0.70:
        status = "healthy"
    elif loss_ratio <= 0.85:
        status = "warning"
    else:
        status = "critical"
    
    return AdminMetricsResponse(
        total_premium=metrics["total_premium"],
        total_payout=metrics["total_payout"],
        loss_ratio=metrics["loss_ratio"],
        loss_ratio_percentage=round(metrics["loss_ratio"] * 100, 2),
        status=status,
        last_updated=metrics["last_updated"],
    )
