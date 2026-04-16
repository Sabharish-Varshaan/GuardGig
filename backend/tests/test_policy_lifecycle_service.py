from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.services.policy_lifecycle_service import update_policy_status


def test_expired_policy_marked_inactive():
    admin = MagicMock()
    admin.table.return_value = admin
    admin.update.return_value = admin
    admin.eq.return_value = admin
    admin.execute.return_value = MagicMock(data=[{"id": "policy-1", "status": "inactive"}])

    policy = {
        "id": "policy-1",
        "status": "active",
        "end_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    }

    updated = update_policy_status(admin, "policies", policy)
    assert updated["status"] == "inactive"
    assert updated["is_active"] is False


def test_non_expired_policy_remains_active():
    admin = MagicMock()

    policy = {
        "id": "policy-2",
        "status": "active",
        "end_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    }

    updated = update_policy_status(admin, "policies", policy)
    assert updated["status"] == "active"
    assert updated["is_active"] is True
