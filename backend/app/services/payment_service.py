from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

logger = logging.getLogger(__name__)


def simulate_razorpay_payout(amount: float, user_id: str) -> dict[str, str]:
    logger.info(f"  [PAYOUT] Simulating payout: amount=₹{amount}, user_id={user_id}")
    transaction_id = f"SIM_TXN_{uuid4().hex[:8].upper()}"
    paid_at = datetime.now(timezone.utc).isoformat()

    logger.info(f"  [PAYOUT] ✓ Simulated transaction created: transaction_id={transaction_id}")
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
    masked_account: str | None,
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