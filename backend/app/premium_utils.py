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
    variance_multiplier = float(income_variance or 0.0) * 0.02
    premium = base + (variance_multiplier * base)
    return round(premium, 2)
