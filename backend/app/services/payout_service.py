from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone

from .payment_service import persist_claim_payment, update_claim_payout_status
from .payout_details_service import fetch_user_payout_details, resolve_claim_payout_destination

logger = logging.getLogger(__name__)


def process_payout(
    claim: dict,
    *,
    admin,
    claims_table: str,
    payout_details_table: str,
    trigger_snapshot: dict,
    delay_range: tuple[float, float] = (1.0, 2.0),
) -> dict:
    claim_id = str(claim.get("id") or "")
    user_id = str(claim.get("user_id") or "")
    payout_amount = float(claim.get("payout_amount") or 0)

    logger.info("[PAYOUT START] claim_id=%s user_id=%s amount=%.2f", claim_id, user_id, payout_amount)

    try:
        update_claim_payout_status(admin, claims_table, claim_id, "processing")

        low, high = delay_range
        if high > 0:
            time.sleep(random.uniform(max(0.0, low), max(0.0, high)))

        payout_details = fetch_user_payout_details(admin, payout_details_table, user_id)
        payout_destination = resolve_claim_payout_destination(payout_details)
        if not payout_destination:
            persist_claim_payment(
                admin,
                claims_table,
                claim_id,
                "pending_payout_details",
                "failed",
                None,
                None,
                "pending",
                None,
                trigger_snapshot,
            )
            logger.error("[PAYOUT FAILED] claim_id=%s reason=missing_payout_details", claim_id)
            return {
                "success": False,
                "payment_status": "pending_payout_details",
                "payout_status": "failed",
                "transaction_id": None,
                "paid_at": None,
                "payout_method": "pending",
                "masked_account": None,
            }

        payout_method, masked_account = payout_destination
        order_id = f"order_{random.randint(1000000000, 9999999999)}"
        payment_id = f"pay_{random.randint(1000000000, 9999999999)}"
        payment_signature = f"sig_{random.randint(1000000000, 9999999999)}"
        transaction_id = f"RZP_{random.randint(1000000000, 9999999999)}"
        paid_at = datetime.now(timezone.utc).isoformat()

        persist_claim_payment(
            admin,
            claims_table,
            claim_id,
            "credited",
            "credited",
            transaction_id,
            paid_at,
            payout_method,
            masked_account,
            trigger_snapshot,
            order_id,
            payment_id,
            payment_signature,
        )
        logger.info("[PAYMENT STORED] order_id=%s payment_id=%s", order_id, payment_id)

        logger.info(
            "[PAYOUT SUCCESS] claim_id=%s transaction_id=%s method=%s",
            claim_id,
            transaction_id,
            payout_method,
        )
        return {
            "success": True,
            "payment_status": "credited",
            "payout_status": "credited",
            "transaction_id": transaction_id,
            "paid_at": paid_at,
            "payout_method": payout_method,
            "masked_account": masked_account,
            "order_id": order_id,
            "payment_id": payment_id,
            "payment_signature": payment_signature,
        }
    except Exception as exc:
        logger.exception("[PAYOUT FAILED] claim_id=%s reason=unexpected_error error=%s", claim_id, str(exc))
        try:
            persist_claim_payment(
                admin,
                claims_table,
                claim_id,
                "failed",
                "failed",
                None,
                None,
                "pending",
                None,
                trigger_snapshot,
            )
        except Exception:
            update_claim_payout_status(admin, claims_table, claim_id, "failed")

        return {
            "success": False,
            "payment_status": "failed",
            "payout_status": "failed",
            "transaction_id": None,
            "paid_at": None,
            "payout_method": "pending",
            "masked_account": None,
            "order_id": None,
            "payment_id": None,
            "payment_signature": None,
        }
