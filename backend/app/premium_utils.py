
import logging

from ml.predict import get_risk_score

from .trigger_utils import get_7day_forecast, resolve_coordinates


logger = logging.getLogger(__name__)


TARGET_BCR = 0.65
MAX_BCR = 0.70
MIN_PREMIUM = 20.0
MAX_PREMIUM = 50.0
MIN_COVERAGE_FLOOR = 150.0
TARGET_INCOME_REPLACEMENT = 0.40
MAX_COVERAGE_REPLACEMENT = 0.60


def _trigger_probability_from_risk(risk_score: float) -> float:
    """Map ML risk score in [0, 1] to trigger probability via direct clamping.

    Clamps probability to [0.1, 0.3] without inverse mapping.
    Ensures strict BCR target of 0.65 is achievable.
    """
    return round(max(0.1, min(0.3, float(risk_score or 0.0))), 4)


def _calculate_bcr_pricing_from_probability(mean_income: float, trigger_probability: float) -> tuple[float, float, float]:
    """Calculate premium and coverage using meaningful-coverage-first BCR math."""
    income = float(mean_income or 0.0)
    prob = max(0.1, min(0.3, float(trigger_probability or 0.0)))

    target_coverage = max(income * TARGET_INCOME_REPLACEMENT, MIN_COVERAGE_FLOOR)
    target_coverage = min(target_coverage, income * MAX_COVERAGE_REPLACEMENT)

    required_premium = (target_coverage * prob) / TARGET_BCR
    premium = max(MIN_PREMIUM, min(required_premium, MAX_PREMIUM))

    coverage = (premium * TARGET_BCR) / prob
    coverage = min(coverage, income * MAX_COVERAGE_REPLACEMENT)

    reason = (
        "Optimal protection (40%) achieved"
        if premium >= required_premium
        else "Adjusted for risk (sustainability mode)"
    )

    if income > 0:
        protection_pct = round((coverage / income) * 100, 1)
    else:
        protection_pct = 0.0

    premium = round(premium, 2)
    coverage = round(coverage, 2)

    expected_payout = coverage * prob
    loss_ratio = (expected_payout / premium) if premium > 0 else 0.0
    if loss_ratio > MAX_BCR:
        logger.warning(
            "[PRICING WARNING] bcr_ceiling_exceeded income=%s prob=%s premium=%s coverage=%s loss_ratio=%.4f",
            income,
            prob,
            premium,
            coverage,
            loss_ratio,
        )

    print(
        "[MEANINGFUL PRICING]",
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
    """Calculate premium and coverage using target-coverage-first BCR math."""
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
    target_coverage = round(
        min(
            max(mean_income * TARGET_INCOME_REPLACEMENT, MIN_COVERAGE_FLOOR),
            mean_income * MAX_COVERAGE_REPLACEMENT,
        ),
        2,
    )
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
