from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import NotificationMarkReadResponse, NotificationResponse, NotificationsListResponse
from ..services.notification_service import list_notifications, mark_notification_read
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api", tags=["notifications"])


@router.get("/notifications/me", response_model=NotificationsListResponse)
def get_my_notifications(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    rows = list_notifications(admin, settings.supabase_notifications_table, current_user["id"])
    notifications = [NotificationResponse(**item) for item in rows]
    return NotificationsListResponse(notifications=notifications)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationMarkReadResponse)
def mark_my_notification_read(notification_id: str, current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    updated = mark_notification_read(admin, settings.supabase_notifications_table, notification_id, current_user["id"])
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return NotificationMarkReadResponse(
        notification=NotificationResponse(**updated),
        message="Notification marked as read",
    )
