from __future__ import annotations

from datetime import datetime, timezone


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def update_policy_status(admin, policies_table: str, policy: dict) -> dict:
    now_utc = datetime.now(timezone.utc)
    end_date = _parse_iso_datetime(policy.get("end_date") or policy.get("expires_at"))
    is_expired = end_date is not None and now_utc > end_date

    updated = dict(policy)
    if is_expired and str(policy.get("status") or "").lower() != "inactive":
        response = (
            admin.table(policies_table)
            .update({"status": "inactive", "updated_at": now_utc.isoformat()})
            .eq("id", policy.get("id"))
            .execute()
        )
        rows = response.data or []
        updated = rows[0] if rows else updated
        updated["status"] = "inactive"

    updated["is_active"] = str(updated.get("status") or "").lower() == "active" and not is_expired
    return updated
