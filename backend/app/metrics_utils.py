"""
Actuarial metrics utilities for tracking system-wide premiums, payouts, and loss ratio.
"""

import logging
from datetime import datetime, timezone

from .config import get_settings

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


def _compute_source_totals(admin) -> tuple[float, float, float]:
    """Compute totals from source-of-truth transactional tables."""
    settings = get_settings()

    paid_policies = (
        admin.table(settings.supabase_policies_table)
        .select("premium")
        .eq("payment_status", "success")
        .execute()
        .data
        or []
    )
    paid_claims = (
        admin.table(settings.supabase_claims_table)
        .select("payout_amount")
        .eq("payment_status", "paid")
        .execute()
        .data
        or []
    )

    total_premium = round(sum(float(row.get("premium") or 0) for row in paid_policies), 2)
    total_payout = round(sum(float(row.get("payout_amount") or 0) for row in paid_claims), 2)
    loss_ratio = _calculate_loss_ratio(total_premium, total_payout)
    return total_premium, total_payout, loss_ratio


def _reconcile_metrics_if_needed(admin, metrics: dict, metrics_table: str) -> dict:
    """Reconcile cached metrics row with transactional totals when drift is detected."""
    source_premium, source_payout, source_ratio = _compute_source_totals(admin)

    cached_premium = float(metrics.get("total_premium", 0) or 0)
    cached_payout = float(metrics.get("total_payout", 0) or 0)
    cached_ratio = float(metrics.get("loss_ratio", 0) or 0)

    has_drift = (
        abs(cached_premium - source_premium) > 0.01
        or abs(cached_payout - source_payout) > 0.01
        or abs(cached_ratio - source_ratio) > 0.0001
    )

    if not has_drift:
        return {
            "total_premium": cached_premium,
            "total_payout": cached_payout,
            "loss_ratio": cached_ratio,
            "last_updated": metrics.get("last_updated", datetime.now(timezone.utc).isoformat()),
        }

    admin.table(metrics_table).update({
        "total_premium": source_premium,
        "total_payout": source_payout,
        "loss_ratio": source_ratio,
        "updated_by": "metrics_reconciler",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }).eq("id", 1).execute()

    logger.warning(
        "[METRICS] Reconciled drift: cached(premium=%s, payout=%s, ratio=%s) -> source(premium=%s, payout=%s, ratio=%s)",
        cached_premium,
        cached_payout,
        cached_ratio,
        source_premium,
        source_payout,
        source_ratio,
    )

    refreshed = admin.table(metrics_table).select("*").eq("id", 1).execute().data or []
    row = refreshed[0] if refreshed else {}
    return {
        "total_premium": float(row.get("total_premium", source_premium) or source_premium),
        "total_payout": float(row.get("total_payout", source_payout) or source_payout),
        "loss_ratio": float(row.get("loss_ratio", source_ratio) or source_ratio),
        "last_updated": row.get("last_updated", datetime.now(timezone.utc).isoformat()),
    }


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
        return _reconcile_metrics_if_needed(admin, metrics, metrics_table)
    except Exception as exc:
        logger.error(f"[METRICS] Failed to fetch full metrics: {exc}")
        return {
            "total_premium": 0.0,
            "total_payout": 0.0,
            "loss_ratio": 0.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


def check_loss_ratio_threshold(
    admin,
    threshold: float = 0.85,
    metrics_table: str = "system_metrics",
    min_total_premium_for_enforcement: float = 500.0,
) -> bool:
    """
    Check if loss ratio exceeds threshold.
    Returns True if within safe bounds (loss_ratio <= threshold).
    Raises ValueError if threshold exceeded (for use in policy creation).
    """
    metrics = _get_or_init_metrics(admin, metrics_table)
    total_premium = float(metrics.get("total_premium", 0) or 0)

    if total_premium < min_total_premium_for_enforcement:
        logger.info(
            "[RISK CONTROL] Skipping loss-ratio block: total_premium=₹%.2f < min_enforcement=₹%.2f",
            total_premium,
            min_total_premium_for_enforcement,
        )
        return True

    loss_ratio = get_current_loss_ratio(admin, metrics_table)
    
    if loss_ratio > threshold:
        logger.warning(f"[RISK CONTROL] Loss ratio {loss_ratio:.2%} exceeds threshold {threshold:.2%} - blocking policies")
        raise ValueError(f"System risk exposure too high (loss_ratio {loss_ratio:.2%}). New policies temporarily blocked.")
    
    logger.debug(f"[RISK CONTROL] Loss ratio {loss_ratio:.2%} within safe bounds")
    return True
