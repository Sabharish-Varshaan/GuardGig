import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=IST)
    return parsed.astimezone(IST)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def enforce_waiting_period(policy: dict, waiting_hours: int = 24) -> None:
    created_at = _parse_dt(policy.get("created_at"))
    policy_date = _parse_date(policy.get("policy_start_date"))

    if created_at is None and policy_date is not None:
        created_at = datetime.combine(policy_date, time.min, tzinfo=IST)

    if created_at is None:
        logger.debug("  [WAITING PERIOD] No created_at or policy_start_date found, skipping check")
        return

    eligible_at = created_at + timedelta(hours=int(policy.get("waiting_period_hours", waiting_hours)))
    if datetime.now(IST) < eligible_at:
        hours_remaining = (eligible_at - datetime.now(IST)).total_seconds() / 3600
        logger.warning(f"  [WAITING PERIOD] Not eligible yet ({hours_remaining:.1f} hours remaining)")
        raise ValueError("Waiting period of 24 hours is not completed")
    
    logger.debug(f"  [WAITING PERIOD] ✓ Waiting period satisfied (created={created_at.isoformat()})")


def _extract_claim_count(response) -> int:
    data = response.data

    if data is None:
        return 0

    if isinstance(data, int):
        return int(data)

    if isinstance(data, list):
        if not data:
            return 0

        row = data[0]
        if isinstance(row, dict):
            value = row.get("claims_today")
            if value is None:
                return 0
            return int(value)

    if isinstance(data, dict):
        value = data.get("claims_today")
        if value is None:
            return 0
        return int(value)

    return 0


def get_claims_today_count_ist(admin, claims_table: str, user_id: str) -> int:
    """Count a user's claims for the current IST day."""
    try:
        response = admin.rpc("guardgig_claims_today_count_ist", {"p_user_id": user_id}).execute()
        return _extract_claim_count(response)
    except Exception:
        now = datetime.now(IST)
        day_start = datetime.combine(now.date(), time.min, tzinfo=IST)
        next_day = day_start + timedelta(days=1)

        response = (
            admin.table(claims_table)
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("created_at", day_start.isoformat())
            .lt("created_at", next_day.isoformat())
            .execute()
        )

        if getattr(response, "count", None) is not None:
            return int(response.count)

        return len(response.data or [])


def enforce_max_one_claim_per_day(admin, claims_table: str, user_id: str) -> int:
    count = get_claims_today_count_ist(admin, claims_table, user_id)
    logger.debug(f"  [DAILY LIMIT] Claims created today for user {user_id}: {count}")

    if count >= 1:
        logger.warning(f"  [DAILY LIMIT] ✗ Daily claim limit reached ({count} >= 1)")
        raise ValueError("Daily claim limit reached")

    logger.debug(f"  [DAILY LIMIT] ✓ User has created {count} claims today (limit: 1)")
    return count


def fetch_recent_claim_count(admin, claims_table: str, user_id: str, lookback_days: int = 30) -> int:
    since = (datetime.now(IST) - timedelta(days=lookback_days)).isoformat()
    response = (
        admin.table(claims_table)
        .select("id")
        .eq("user_id", user_id)
        .gte("created_at", since)
        .execute()
    )
    return len(response.data or [])


def calculate_fraud_score(activity_status: str, location_valid: bool, claim_frequency: int) -> float:
    """Calculate fraud score.

    This function will attempt to use a trained fraud model (if present) via
    `backend.ml.predict.get_fraud_score`. If not available or prediction fails,
    the previous heuristic is used.
    """
    claim_frequency = max(0, claim_frequency)

    try:
        # lazy import to avoid hard dependency when models are not present
        from ml.predict import get_fraud_score

        features = {
            "number_of_claims_today": float(claim_frequency),
            "time_since_last_claim": 0.0,  # unknown in this call site; keep 0 as conservative estimate
            "location_change": 0.0 if location_valid else 1.0,
            "activity_status": activity_status,
        }
        score = float(get_fraud_score(features))
        score = min(1.0, max(0.0, round(score, 2)))
        logger.debug(f"  [FRAUD] Calculated via ML model: {score:.2f} (activity={activity_status}, claims={claim_frequency}, location={'valid' if location_valid else 'invalid'})")
        return score
    except Exception as e:
        # Fallback to previous heuristic
        logger.debug(f"  [FRAUD] ML model unavailable ({str(e)[:50]}), using heuristic")
        score = min(0.5, claim_frequency / 20.0)

        if activity_status.lower() in {"none", "inactive", "no_activity", "suspicious"}:
            score += 0.4

        if not location_valid:
            score += 0.3

        final_score = min(1.0, round(score, 2))
        logger.debug(f"  [FRAUD] Heuristic result: {final_score:.2f} (activity={activity_status}, claims={claim_frequency}, location={'valid' if location_valid else 'invalid'})")
        return final_score


def enforce_exclusions(activity_status: str, location_valid: bool, fraud_score: float, fraud_threshold: float) -> None:
    if activity_status.lower() in {"inactive", "suspicious"}:
        logger.warning(f"  [EXCLUSIONS] ✗ Claim excluded: activity_status={activity_status} (inactive/suspicious)")
        raise ValueError("Claim excluded: inactive or suspicious activity")
    if activity_status.lower() in {"none", "no_activity"}:
        logger.warning(f"  [EXCLUSIONS] ✗ Claim excluded: activity_status={activity_status} (no activity)")
        raise ValueError("Claim excluded: no activity")
    if not location_valid:
        logger.warning(f"  [EXCLUSIONS] ✗ Claim excluded: location_valid={location_valid}")
        raise ValueError("Claim excluded: invalid location")
    if fraud_score > fraud_threshold:
        logger.warning(f"  [EXCLUSIONS] ✗ Claim excluded: fraud_score={fraud_score:.2f} > threshold={fraud_threshold:.2f}")
        raise ValueError("Claim excluded: fraud risk too high")
    
    logger.debug(f"  [EXCLUSIONS] ✓ All exclusion checks passed (activity={activity_status}, location={location_valid}, fraud={fraud_score:.2f})")
