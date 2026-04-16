
from ml.predict import get_risk_score


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


def calculate_premium(income: float, risk_preference: str = "Medium", income_variance: float = 0.0, *, rain: float = 0.0, aqi: float = 0.0, lat: float | None = None, lon: float | None = None) -> float:
    """Calculate premium using trigger probability and income.

    - `income` is treated as mean daily income.
    - risk_preference/rain/aqi/location args are retained for API compatibility.
    """
    _ = risk_preference  # Retained for API compatibility.
    _ = lat
    _ = lon

    risk_score = calculate_policy_risk_score(
        income,
        income_variance,
        rain=rain,
        aqi=aqi,
    )

    if risk_score < 0.3:
        trigger_probability = 0.02
    elif risk_score < 0.6:
        trigger_probability = 0.05
    else:
        trigger_probability = 0.08

    premium = trigger_probability * float(income or 0.0) * 7
    premium = max(20.0, min(premium, 50.0))
    return round(premium, 2)
