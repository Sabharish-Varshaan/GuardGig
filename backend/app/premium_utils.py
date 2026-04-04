
from ml.predict import get_risk_score


def calculate_premium(income: float, risk_preference: str = "Medium", income_variance: float = 0.0, *, rain: float = 0.0, aqi: float = 0.0, lat: float | None = None, lon: float | None = None) -> float:
    """Calculate premium combining ML risk score and income variance.

    - `income` is expected to be weekly income (existing API contract).
    - risk_preference/rain/aqi/location args are used in ML feature set.
    """
    _ = risk_preference  # Retained for API compatibility.
    _ = lat
    _ = lon

    base = income * 0.006
    
    # Prepare features for ML model
    features = {
        "mean_income": float(income or 0.0),
        "income_variance": float(income_variance or 0.0),
        "rain": float(rain or 0.0),
        "aqi": float(aqi or 0.0),
    }

    # Get ML risk score
    try:
        risk_score = float(get_risk_score(features))
    except Exception:
        risk_score = 0.0

    # Combined formula: base * (1 + risk_score + variance_factor)
    variance_factor = income_variance * 0.02
    premium = base * (1 + risk_score + variance_factor)
    
    print("ML risk_score:", risk_score)
    print("Variance:", income_variance)
    print("Final premium:", round(premium, 2))
    
    return round(premium, 2)
