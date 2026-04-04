from ml.predict import get_risk_score


def calculate_premium(income: float, risk_preference: str = "Medium", income_variance: float = 0.0, *, rain: float = 0.0, aqi: float = 0.0, lat: float | None = None, lon: float | None = None) -> float:
    """Calculate premium from weekly income and income variance.

    - `income` is expected to be weekly income (existing API contract).
    - risk_preference/rain/aqi/location args are retained for API compatibility.
    """
    _ = risk_preference  # Retained for API compatibility.
    _ = rain
    _ = aqi
    _ = lat
    _ = lon

    base = income * 0.006
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

    print("ML risk_score:", risk_score)
    premium = base * (1 + risk_score)
    return round(premium, 2)
