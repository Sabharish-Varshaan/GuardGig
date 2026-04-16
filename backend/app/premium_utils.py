
import logging

from ml.predict import get_risk_score


logger = logging.getLogger(__name__)


def calculate_policy_risk_score(income: float, income_variance: float = 0.0, *, rain: float = 0.0, aqi: float = 0.0) -> float:
    """Calculate policy risk score in [0, 1] from underwriting features."""
    features = {
        "mean_income": float(income or 0.0),
        "income_variance": float(income_variance or 0.0),
        "rain": float(rain or 0.0),
        "aqi": float(aqi or 0.0),
    }

    try:
        risk_score = float(get_risk_score(features))
    except Exception:
        risk_score = 0.0

    return max(0.0, min(1.0, round(risk_score, 4)))


def calculate_coverage_amount(
    income: float,
    income_variance: float = 0.0,
    *,
    rain: float = 0.0,
    aqi: float = 0.0,
    risk_score: float | None = None,
) -> float:
    """Calculate coverage from mean income and ML risk score.

    coverage = mean_income * 7 * (0.6 + 0.8 * risk_score)
    """
    mean_income = float(income or 0.0)
    if risk_score is None:
        risk_score = calculate_policy_risk_score(
            mean_income,
            income_variance,
            rain=rain,
            aqi=aqi,
        )
    else:
        risk_score = max(0.0, min(1.0, float(risk_score)))

    coverage = mean_income * 7.0 * (0.6 + 0.8 * risk_score)
    return round(max(0.0, coverage), 2)


def calculate_premium(income: float, risk_preference: str = "Medium", income_variance: float = 0.0, *, rain: float = 0.0, aqi: float = 0.0, lat: float | None = None, lon: float | None = None, risk_score: float | None = None) -> float:
    """Calculate premium from ML-driven coverage and risk score.

    - `income` is treated as mean daily income.
    - risk_preference/location args are retained for API compatibility.
    """
    _ = risk_preference  # Retained for API compatibility.
    _ = lat
    _ = lon

    mean_income = float(income or 0.0)
    if risk_score is None:
        risk_score = calculate_policy_risk_score(
            mean_income,
            income_variance,
            rain=rain,
            aqi=aqi,
        )
    else:
        risk_score = max(0.0, min(1.0, float(risk_score)))

    coverage_amount = calculate_coverage_amount(
        mean_income,
        income_variance,
        rain=rain,
        aqi=aqi,
        risk_score=risk_score,
    )

    premium = coverage_amount * risk_score * 0.1
    premium = max(15.0, min(premium, 80.0))
    premium = round(premium, 2)

    logger.info(
        "[PREMIUM] income=%s, risk=%s, coverage=%s, premium=%s",
        mean_income,
        risk_score,
        coverage_amount,
        premium,
    )
    return premium
