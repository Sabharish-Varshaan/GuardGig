from __future__ import annotations

from datetime import datetime, timezone


def create_notification(
    admin,
    notifications_table: str,
    *,
    user_id: str,
    title: str,
    message: str,
    notification_type: str,
    claim_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    payload = {
        "user_id": user_id,
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "claim_id": claim_id,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    response = admin.table(notifications_table).insert(payload).execute()
    rows = response.data or []
    return rows[0] if rows else {}


def list_notifications(admin, notifications_table: str, user_id: str, limit: int = 50) -> list[dict]:
    response = (
        admin.table(notifications_table)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def mark_notification_read(admin, notifications_table: str, notification_id: str, user_id: str) -> dict | None:
    response = (
        admin.table(notifications_table)
        .update({"read_status": True})
        .eq("id", notification_id)
        .eq("user_id", user_id)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None
