from datetime import date, datetime, time, timedelta, timezone


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def enforce_waiting_period(policy: dict, waiting_hours: int = 24) -> None:
    created_at = _parse_dt(policy.get("created_at"))
    policy_date = _parse_date(policy.get("policy_start_date"))

    if created_at is None and policy_date is not None:
        created_at = datetime.combine(policy_date, time.min, tzinfo=timezone.utc)

    if created_at is None:
        return

    eligible_at = created_at + timedelta(hours=int(policy.get("waiting_period_hours", waiting_hours)))
    if datetime.now(timezone.utc) < eligible_at:
        raise ValueError("Waiting period of 24 hours is not completed")


def enforce_max_one_claim_per_day(admin, claims_table: str, user_id: str) -> None:
    now = datetime.now(timezone.utc)
    day_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    next_day = day_start + timedelta(days=1)

    response = (
        admin.table(claims_table)
        .select("id")
        .eq("user_id", user_id)
        .gte("created_at", day_start.isoformat())
        .lt("created_at", next_day.isoformat())
        .limit(1)
        .execute()
    )

    if response.data:
        raise ValueError("Maximum one claim per day is allowed")


def fetch_recent_claim_count(admin, claims_table: str, user_id: str, lookback_days: int = 30) -> int:
    since = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
    response = (
        admin.table(claims_table)
        .select("id")
        .eq("user_id", user_id)
        .gte("created_at", since)
        .execute()
    )
    return len(response.data or [])


def calculate_fraud_score(activity_status: str, location_valid: bool, claim_frequency: int) -> float:
    score = min(0.5, claim_frequency / 20.0)

    if activity_status.lower() in {"none", "inactive", "no_activity"}:
        score += 0.4

    if not location_valid:
        score += 0.3

    return min(1.0, round(score, 2))


def enforce_exclusions(activity_status: str, location_valid: bool, fraud_score: float, fraud_threshold: float) -> None:
    if activity_status.lower() in {"none", "inactive", "no_activity"}:
        raise ValueError("Claim excluded: no activity")
    if not location_valid:
        raise ValueError("Claim excluded: invalid location")
    if fraud_score > fraud_threshold:
        raise ValueError("Claim excluded: fraud risk too high")
