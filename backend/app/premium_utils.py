from ml.predict import get_risk_score


def calculate_premium(income: float, risk_preference: str = "Medium", income_variance: float = 0.0, *, rain: float = 0.0, aqi: float = 0.0, lat: float | None = None, lon: float | None = None) -> float:
    """Calculate premium from weekly income and variance multiplier.

    This function integrates a learned risk model. If the model is not available,
    `get_risk_score` will fall back to a heuristic.

    - `income` is expected to be weekly income (this is the existing API).
    - internally we convert to mean_income per day for the model.
    """
    _ = risk_preference  # Retained for API compatibility.

    # Derive mean income per day from weekly income (existing code passes weekly_income)
    mean_income = float(income) / 7.0

    features = {
        "mean_income": mean_income,
        "income_variance": float(income_variance or 0.0),
        "rain": float(rain or 0.0),
        "aqi": float(aqi or 0.0),
        "lat": lat,
        "lon": lon,
    }

    risk_score = get_risk_score(features)

    base = income * 0.006
    premium = base * (1.0 + float(risk_score))
    return round(premium, 2)
