
import logging

from ml.predict import get_risk_score

from .trigger_utils import get_7day_forecast, resolve_coordinates


logger = logging.getLogger(__name__)


def _trigger_probability_from_risk(risk_score: float) -> float:
    """Map ML risk score in [0, 1] to trigger probability.

    Lower risk yields higher trigger probability under this actuarial profile,
    which keeps coverage conservative for low-risk cohorts after BCR control.
    """
    return round(0.08 - (0.06 * risk_score), 4)


def _calculate_bcr_pricing_from_probability(mean_income: float, trigger_probability: float) -> tuple[float, float, float]:
    """Calculate premium and coverage with a fixed actuarial BCR target.

    Returns (premium, coverage, normalized_trigger_probability).
    """
    safe_trigger_probability = float(trigger_probability or 0.0)
    if safe_trigger_probability <= 0.0:
        safe_trigger_probability = 0.05

    raw_premium = safe_trigger_probability * mean_income * 3.0
    premium = max(20.0, min(raw_premium, 50.0))

    target_bcr = 0.65
    coverage = (premium * target_bcr) / safe_trigger_probability
    coverage = min(coverage, mean_income * 1.5)

    premium = round(premium, 2)
    coverage = round(max(0.0, coverage), 2)

    expected_payout = coverage * safe_trigger_probability
    loss_ratio = (expected_payout / premium) if premium > 0 else 0.0
    print(
        f"[ACTUARIAL CHECK] premium={premium}, coverage={coverage}, "
        f"prob={safe_trigger_probability}, loss_ratio={loss_ratio}"
    )

    return premium, coverage, safe_trigger_probability


def _calculate_bcr_pricing(mean_income: float, risk_score: float) -> tuple[float, float]:
    """Calculate premium and coverage using a BCR-oriented sequence.

    1) premium = trigger_probability * mean_income * 3
    2) premium bounded to [20, 50]
    3) coverage = (premium / trigger_probability) * 0.65
    4) both rounded to 2 decimals
    """
    trigger_probability = _trigger_probability_from_risk(risk_score)
    premium, coverage, _ = _calculate_bcr_pricing_from_probability(mean_income, trigger_probability)
    return premium, coverage


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
