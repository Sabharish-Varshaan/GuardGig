from __future__ import annotations

import logging
from datetime import datetime, timezone

import razorpay

from ..config import get_settings

logger = logging.getLogger(__name__)


def _build_client() -> razorpay.Client:
    settings = get_settings()

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise RuntimeError("Razorpay credentials are not configured")

    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def simulate_razorpay_payout(amount: float, user_id: str) -> dict[str, str]:
    logger.info(f"  [PAYOUT] Creating Razorpay order: amount=₹{amount}, user_id={user_id}")
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
    
    logger.info(f"  [PAYOUT] ✓ Order created: transaction_id={transaction_id}, amount_paise={amount_paise}")
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
    logger.debug(f"  [PERSIST] Saving payout to claim {claim_id}: status={payment_status}, transaction_id={transaction_id}")
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
    result = rows[0] if rows else {}
    if result:
        logger.debug(f"  [PERSIST] ✓ Payout persisted: claim_id={claim_id}, status={payment_status}")
    return result