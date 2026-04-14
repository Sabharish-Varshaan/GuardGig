from __future__ import annotations

import logging
from datetime import datetime, timezone
import random

logger = logging.getLogger(__name__)


def simulate_razorpay_payout(amount: float, user_id: str) -> dict[str, str]:
    logger.info(f"  [PAYOUT] Simulating payout: amount=₹{amount}, user_id={user_id}")
    transaction_id = f"TXN_{random.randint(100000, 999999)}"
    paid_at = datetime.now(timezone.utc).isoformat()

    logger.info(f"  [PAYOUT] ✓ Simulated transaction created: transaction_id={transaction_id}")
    return {
        "status": "credited",
        "transaction_id": transaction_id,
        "paid_at": paid_at,
    }


def normalize_payout_method(payout_method: str | None) -> str:
    method = str(payout_method or "pending").strip().lower()
    if method == "upi":
        return "UPI"
    if method == "bank":
        return "BANK"
    return "pending"


def persist_claim_payment(
    admin,
    claims_table: str,
    claim_id: str,
    payment_status: str,
    transaction_id: str | None,
    paid_at: str | None,
    payout_method: str,
    masked_account: str | None,
    trigger_snapshot: dict,
) -> dict:
    normalized_method = normalize_payout_method(payout_method)
    logger.debug(f"  [PERSIST] Saving payout to claim {claim_id}: status={payment_status}, transaction_id={transaction_id}")
    response = (
        admin.table(claims_table)
        .update(
            {
                "payment_status": payment_status,
                "transaction_id": transaction_id,
                "paid_at": paid_at,
                "payout_method": normalized_method,
                "masked_account": masked_account,
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