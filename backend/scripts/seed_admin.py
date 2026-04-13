"""Seed the GuardGig admin account.

Usage:
    cd backend
    .venv/bin/python scripts/seed_admin.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth_utils import hash_password
from app.config import get_settings
from app.supabase_client import get_admin_client

ADMIN_EMAIL = "admin@guardgig.com"
ADMIN_PASSWORD = "admin123"
ADMIN_FULL_NAME = "GuardGig Admin"
ADMIN_PHONE = "9999999999"


def main() -> None:
    settings = get_settings()
    admin = get_admin_client()

    payload = {
        "full_name": ADMIN_FULL_NAME,
        "phone": ADMIN_PHONE,
        "email": ADMIN_EMAIL,
        "password_hash": hash_password(ADMIN_PASSWORD),
        "role": "admin",
    }

    response = (
        admin.table(settings.supabase_users_table)
        .upsert(payload, on_conflict="email")
        .execute()
    )

    rows = response.data or []
    if rows:
        seeded_user = rows[0]
        print(f"Seeded admin user: {seeded_user.get('email', ADMIN_EMAIL)}")
    else:
        print(f"Seeded admin user: {ADMIN_EMAIL}")


if __name__ == "__main__":
    main()
