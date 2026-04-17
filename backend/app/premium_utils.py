
import logging
import math

from ml.predict import get_risk_score

from .trigger_utils import get_7day_forecast, resolve_coordinates


logger = logging.getLogger(__name__)


def _trigger_probability_from_risk(risk_score: float) -> float:
    """Map ML risk score in [0, 1] to trigger probability via direct clamping.

    Clamps probability to [0.1, 0.3] without inverse mapping.
    Ensures strict BCR target of 0.65 is achievable.
    """
    return round(max(0.1, min(0.3, float(risk_score or 0.0))), 4)


def _calculate_bcr_pricing_from_probability(mean_income: float, trigger_probability: float) -> tuple[float, float, float]:
    """Calculate premium and coverage with nonlinear premium scaling and BCR constraints.

    - Premium uses sqrt-normalized income: prob * sqrt(income) * K
    - Premium is bounded to [20, 50]
    - Coverage targets 40% income when affordable at BCR 0.65
    - Coverage targets 40% income when sustainable, else falls back to BCR-safe
    - Coverage is capped at 60% and has a soft high-risk floor (without breaking BCR)
    - Returns (premium, coverage, clamped_trigger_probability)
    """
    income = float(mean_income or 0.0)
    prob = max(0.1, min(0.3, float(trigger_probability or 0.0)))

    target_bcr = 0.65
    max_loss_ratio = 0.7
    premium_tuning_constant = 5.2
    normalized_income = math.sqrt(max(0.0, income))
    base_premium = prob * normalized_income * premium_tuning_constant
    premium = base_premium * (0.7 + 0.5 * prob)
    premium = max(20.0, min(premium, 50.0))

    print(
        "[PREMIUM TUNED]",
        {
            "income": income,
            "prob": prob,
            "premium": round(premium, 2),
        },
    )

    target_coverage = income * 0.4
    min_coverage = income * 0.2
    max_coverage = income * 0.6

    # For low-risk users, uplift premium up to the level needed for 40% coverage
    # at the safety threshold, while still respecting the [20, 50] bounds.
    required_target_premium = (target_coverage * prob) / max_loss_ratio if max_loss_ratio > 0 else 50.0
    if prob <= 0.12 and required_target_premium <= 50.0:
        premium = max(premium, min(required_target_premium + 0.01, 50.0))

    target_loss_ratio = (target_coverage * prob) / premium if premium > 0 else float("inf")
    if target_loss_ratio <= max_loss_ratio:
        coverage = target_coverage
        reason = "Optimal protection (40%) achieved"
    else:
        coverage = (premium * target_bcr) / prob
        reason = "Adjusted for risk (sustainability mode)"

    coverage = min(coverage, max_coverage)

    # Soft high-risk floor: nudge toward 20% minimum only when still BCR-safe.
    soft_floor = min_coverage * 0.9
    if coverage < min_coverage and premium > 0:
        while coverage < soft_floor and premium < 50.0:
            premium = min(premium * 1.1, 50.0)
            target_loss_ratio = (target_coverage * prob) / premium if premium > 0 else float("inf")
            if target_loss_ratio <= max_loss_ratio:
                coverage = target_coverage
                reason = "Optimal protection (40%) achieved"
            else:
                coverage = (premium * target_bcr) / prob
                reason = "Adjusted for risk (sustainability mode)"
            coverage = min(coverage, max_coverage)

        if coverage < min_coverage:
            candidate = max(coverage, soft_floor)
            candidate_loss_ratio = (candidate * prob) / premium
            if candidate_loss_ratio <= max_loss_ratio:
                coverage = candidate
                reason = "High-risk: essential protection mode"

    if income > 0:
        protection_pct = round((coverage / income) * 100, 1)
    else:
        protection_pct = 0.0

    premium = round(premium, 2)
    coverage = round(coverage, 2)

    expected_payout = coverage * prob
    loss_ratio = (expected_payout / premium) if premium > 0 else 0.0
    print(
        "[FINAL PRICING]",
        {
            "income": income,
            "prob": prob,
            "premium": premium,
            "coverage": coverage,
            "coverage_pct": protection_pct,
            "loss_ratio": loss_ratio,
            "reason": reason,
        },
    )

    logger.info(
        "[PRICING EXPLAIN] reason=%s income=%s prob=%s protection_pct=%s loss_ratio=%s",
        reason,
        income,
        prob,
        protection_pct,
        round(loss_ratio, 4),
    )

    return premium, coverage, prob


def _calculate_bcr_pricing(mean_income: float, risk_score: float) -> tuple[float, float]:
    """Calculate premium and coverage using a BCR-oriented sequence.

    1) premium = trigger_probability * sqrt(mean_income) * 5.2, with dampening, bounded to [20, 50]
    2) attempt 40% income coverage when affordable at loss_ratio <= 0.7
    3) otherwise fall back to BCR-safe coverage
    4) enforce coverage guardrails with 60% cap and soft high-risk floor
    """
    trigger_probability = _trigger_probability_from_risk(risk_score)
    premium, coverage, _ = _calculate_bcr_pricing_from_probability(mean_income, trigger_probability)
    return premium, coverage


def calculate_pricing_details(
    income: float,
    income_variance: float = 0.0,
    *,
    rain: float = 0.0,
    aqi: float = 0.0,
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    forecast_data: list[dict] | None = None,
    risk_score: float | None = None,
) -> dict:
    """Return premium, coverage and explainability fields for UI consumption."""
    mean_income = float(income or 0.0)
    if risk_score is None:
        risk_score = calculate_policy_risk_score(
            mean_income,
            income_variance,
            rain=rain,
            aqi=aqi,
            city=city,
            lat=lat,
            lon=lon,
            forecast_data=forecast_data,
        )
    else:
        risk_score = max(0.0, min(1.0, float(risk_score)))

    prob = _trigger_probability_from_risk(risk_score)
    premium, coverage, used_prob = _calculate_bcr_pricing_from_probability(mean_income, prob)
    target_coverage = round(mean_income * 0.4, 2)
    min_balanced_coverage = mean_income * 0.25
    if coverage == target_coverage:
        mode = "optimal"
        reason = "Optimal protection (40%) achieved"
    elif coverage >= min_balanced_coverage:
        mode = "balanced"
        reason = "Adjusted for risk (sustainability mode)"
    else:
        mode = "high-risk"
        reason = "High-risk: essential protection mode"
    coverage_percentage = round((coverage / mean_income) * 100, 1) if mean_income > 0 else 0.0

    return {
        "premium": premium,
        "coverage": coverage,
        "coverage_percentage": coverage_percentage,
        "mode": mode,
        "target": "40%",
        "reason": reason,
        "probability": used_prob,
    }


def _resolve_pricing_forecast(
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    forecast_data: list[dict] | None = None,
) -> list[dict]:
    if isinstance(forecast_data, list) and forecast_data:
        return [row for row in forecast_data if isinstance(row, dict)]

    resolved_lat = lat
    resolved_lon = lon

    if resolved_lat is None or resolved_lon is None:
        coordinates = resolve_coordinates(location=city, lat=lat, lon=lon)
        if coordinates is not None:
            resolved_lat, resolved_lon = coordinates

    if resolved_lat is None or resolved_lon is None:
        return []

    try:
        return get_7day_forecast(float(resolved_lat), float(resolved_lon))
    except Exception as exc:
        logger.warning("[ML PRICING FALLBACK] forecast_fetch_failed=%s", exc)
        return []


def calculate_policy_risk_score(
    income: float,
    income_variance: float = 0.0,
    *,
    rain: float = 0.0,
    aqi: float = 0.0,
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    forecast_data: list[dict] | None = None,
) -> float:
    """Calculate policy risk score in [0, 1] from underwriting features."""
    _ = income
    _ = income_variance
    _ = rain
    _ = aqi
    resolved_forecast = _resolve_pricing_forecast(city=city, lat=lat, lon=lon, forecast_data=forecast_data)

    if not resolved_forecast:
        logger.warning(
            "[ML PRICING FALLBACK] forecast_unavailable=True city=%s lat=%s lon=%s",
            city,
            lat,
            lon,
        )

    features = {"forecast_data": resolved_forecast}

    try:
        risk_score = float(get_risk_score(features))
    except Exception as exc:
        logger.warning("[CRITICAL] ML fallback triggered: %s", exc)
        risk_score = 0.5

    return max(0.0, min(1.0, round(risk_score, 4)))


def calculate_coverage_amount(
    income: float,
    income_variance: float = 0.0,
    *,
    rain: float = 0.0,
    aqi: float = 0.0,
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    forecast_data: list[dict] | None = None,
    risk_score: float | None = None,
) -> float:
    """Calculate coverage from mean income and ML risk score.

    coverage = (premium * 0.65) / trigger_probability
    """
    mean_income = float(income or 0.0)
    if risk_score is None:
        risk_score = calculate_policy_risk_score(
            mean_income,
            income_variance,
            rain=rain,
            aqi=aqi,
            city=city,
            lat=lat,
            lon=lon,
            forecast_data=forecast_data,
        )
    else:
        risk_score = max(0.0, min(1.0, float(risk_score)))

    _, coverage = _calculate_bcr_pricing(mean_income, risk_score)
    return coverage


def calculate_premium(
    income: float,
    risk_preference: str = "Medium",
    income_variance: float = 0.0,
    *,
    rain: float = 0.0,
    aqi: float = 0.0,
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    forecast_data: list[dict] | None = None,
    risk_score: float | None = None,
) -> float:
    """Calculate premium from BCR-based trigger probability and income.

    - `income` is treated as mean daily income.
    - risk_preference/location args are retained for API compatibility.
    """
    _ = risk_preference  # Retained for API compatibility.

    mean_income = float(income or 0.0)
    if risk_score is None:
        risk_score = calculate_policy_risk_score(
            mean_income,
            income_variance,
            rain=rain,
            aqi=aqi,
            city=city,
            lat=lat,
            lon=lon,
            forecast_data=forecast_data,
        )
    else:
        risk_score = max(0.0, min(1.0, float(risk_score)))

    premium, coverage_amount = _calculate_bcr_pricing(mean_income, risk_score)

    logger.info(
        "[PREMIUM] income=%s, risk=%s, coverage=%s, premium=%s",
        mean_income,
        risk_score,
        coverage_amount,
        premium,
    )
    return premium
