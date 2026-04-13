"""
Actuarial metrics utilities for tracking system-wide premiums, payouts, and loss ratio.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _get_or_init_metrics(admin, metrics_table: str = "system_metrics") -> dict:
    """Fetch metrics row, initialize if doesn't exist."""
    try:
        response = admin.table(metrics_table).select("*").eq("id", 1).execute()
        rows = response.data or []
        if rows:
            return rows[0]
        
        # Initialize if missing
        logger.info("[METRICS] Initializing system_metrics row")
        init_response = admin.table(metrics_table).insert({
            "id": 1,
            "total_premium": 0,
            "total_payout": 0,
            "loss_ratio": 0,
        }).execute()
        
        init_rows = init_response.data or []
        return init_rows[0] if init_rows else {"total_premium": 0, "total_payout": 0, "loss_ratio": 0}
    except Exception as exc:
        logger.error(f"[METRICS] Failed to fetch/init metrics: {exc}")
        return {"total_premium": 0, "total_payout": 0, "loss_ratio": 0}


def _calculate_loss_ratio(total_premium: float, total_payout: float) -> float:
    """Calculate loss ratio with zero-division safeguard."""
    if total_premium <= 0:
        return 0.0
    
    ratio = total_payout / total_premium
    # Clamp to [0, 1] range
    return min(1.0, max(0.0, round(ratio, 4)))


def update_metrics_on_premium(admin, premium_amount: float, metrics_table: str = "system_metrics") -> dict:
    """
    Update system metrics after premium payment succeeds.
    Called from payment.py verify_payment() after signature verification passes.
    """
    if premium_amount <= 0:
        logger.warning(f"[METRICS] Ignoring non-positive premium: {premium_amount}")
        return {}
    
    try:
        metrics = _get_or_init_metrics(admin, metrics_table)
        
        new_total_premium = float(metrics.get("total_premium", 0)) + premium_amount
        total_payout = float(metrics.get("total_payout", 0))
        new_loss_ratio = _calculate_loss_ratio(new_total_premium, total_payout)
        
        response = admin.table(metrics_table).update({
            "total_premium": round(new_total_premium, 2),
            "loss_ratio": new_loss_ratio,
            "updated_by": "payment_verify",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }).eq("id", 1).execute()
        
        updated_rows = response.data or []
        updated = updated_rows[0] if updated_rows else {}
        
        logger.info(f"[METRICS] Premium tracked: +₹{premium_amount} | total=₹{new_total_premium:.2f} | loss_ratio={new_loss_ratio:.2%}")
        return updated
    except Exception as exc:
        logger.error(f"[METRICS] Failed to update premium metrics: {exc}")
        return {}


def update_metrics_on_payout(admin, payout_amount: float, metrics_table: str = "system_metrics") -> dict:
    """
    Update system metrics after payout succeeds.
    Called from main.py automated_claim_check() after payout execution succeeds.
    """
    if payout_amount <= 0:
        logger.debug(f"[METRICS] Ignoring non-positive payout: {payout_amount}")
        return {}
    
    try:
        metrics = _get_or_init_metrics(admin, metrics_table)
        
        total_premium = float(metrics.get("total_premium", 0))
        new_total_payout = float(metrics.get("total_payout", 0)) + payout_amount
        new_loss_ratio = _calculate_loss_ratio(total_premium, new_total_payout)
        
        response = admin.table(metrics_table).update({
            "total_payout": round(new_total_payout, 2),
            "loss_ratio": new_loss_ratio,
            "updated_by": "automated_claim_check",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }).eq("id", 1).execute()
        
        updated_rows = response.data or []
        updated = updated_rows[0] if updated_rows else {}
        
        logger.info(f"[METRICS] Payout tracked: +₹{payout_amount} | total=₹{new_total_payout:.2f} | loss_ratio={new_loss_ratio:.2%}")
        return updated
    except Exception as exc:
        logger.error(f"[METRICS] Failed to update payout metrics: {exc}")
        return {}


def get_current_loss_ratio(admin, metrics_table: str = "system_metrics") -> float:
    """
    Fetch current loss ratio from system_metrics.
    Used by policy creation to check if new policies should be allowed.
    Returns safeguarded value [0.0, 1.0].
    """
    try:
        metrics = _get_or_init_metrics(admin, metrics_table)
        loss_ratio = float(metrics.get("loss_ratio", 0))
        return min(1.0, max(0.0, loss_ratio))
    except Exception as exc:
        logger.error(f"[METRICS] Failed to fetch loss ratio: {exc}")
        return 0.0


def get_full_metrics(admin, metrics_table: str = "system_metrics") -> dict:
    """
    Fetch complete metrics for admin dashboard.
    Returns all fields with defaults if fetch fails.
    """
    try:
        metrics = _get_or_init_metrics(admin, metrics_table)
        return {
            "total_premium": float(metrics.get("total_premium", 0)),
            "total_payout": float(metrics.get("total_payout", 0)),
            "loss_ratio": float(metrics.get("loss_ratio", 0)),
            "last_updated": metrics.get("last_updated", datetime.now(timezone.utc).isoformat()),
        }
    except Exception as exc:
        logger.error(f"[METRICS] Failed to fetch full metrics: {exc}")
        return {
            "total_premium": 0.0,
            "total_payout": 0.0,
            "loss_ratio": 0.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


def check_loss_ratio_threshold(admin, threshold: float = 0.85, metrics_table: str = "system_metrics") -> bool:
    """
    Check if loss ratio exceeds threshold.
    Returns True if within safe bounds (loss_ratio <= threshold).
    Raises ValueError if threshold exceeded (for use in policy creation).
    """
    loss_ratio = get_current_loss_ratio(admin, metrics_table)
    
    if loss_ratio > threshold:
        logger.warning(f"[RISK CONTROL] Loss ratio {loss_ratio:.2%} exceeds threshold {threshold:.2%} - blocking policies")
        raise ValueError(f"System risk exposure too high (loss_ratio {loss_ratio:.2%}). New policies temporarily blocked.")
    
    logger.debug(f"[RISK CONTROL] Loss ratio {loss_ratio:.2%} within safe bounds")
    return True
