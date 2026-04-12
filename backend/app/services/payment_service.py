from __future__ import annotations

from datetime import datetime, timezone

import razorpay

from ..config import get_settings


def _build_client() -> razorpay.Client:
    settings = get_settings()

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise RuntimeError("Razorpay credentials are not configured")

    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def simulate_razorpay_payout(amount: float, user_id: str) -> dict[str, str]:
    client = _build_client()
    amount_paise = max(1, int(round(float(amount) * 100)))

    order = client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "user_id": user_id,
                "mode": "test",
                "source": "guardgig_claim_payout",
            },
        }
    )

    transaction_id = str(order.get("id") or "")
    paid_at = datetime.now(timezone.utc).isoformat()

    return {
        "status": "paid",
        "transaction_id": transaction_id,
        "paid_at": paid_at,
    }


def persist_claim_payment(
    admin,
    claims_table: str,
    claim_id: str,
    payment_status: str,
    transaction_id: str | None,
    paid_at: str | None,
    payout_method: str,
    trigger_snapshot: dict,
) -> dict:
    response = (
        admin.table(claims_table)
        .update(
            {
                "payment_status": payment_status,
                "transaction_id": transaction_id,
                "paid_at": paid_at,
                "payout_method": payout_method,
                "trigger_snapshot": trigger_snapshot,
            }
        )
        .eq("id", claim_id)
        .execute()
    )

    rows = response.data or []
    return rows[0] if rows else {}