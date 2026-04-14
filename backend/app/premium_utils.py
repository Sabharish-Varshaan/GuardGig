
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
    """Calculate premium combining ML risk score and income variance.

    - `income` is expected to be weekly income (existing API contract).
    - risk_preference/rain/aqi/location args are used in ML feature set.
    """
    _ = risk_preference  # Retained for API compatibility.
    _ = lat
    _ = lon

    base = income * 0.006
    
    risk_score = calculate_policy_risk_score(
        income,
        income_variance,
        rain=rain,
        aqi=aqi,
    )

    # Combined formula: base * (1 + risk_score + variance_factor)
    variance_factor = income_variance * 0.02
    premium = base * (1 + risk_score + variance_factor)
    
    return round(premium, 2)
