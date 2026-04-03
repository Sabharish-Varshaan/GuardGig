def calculate_premium(income: float, risk_preference: str = "Medium", income_variance: float = 0.0) -> float:
    """Calculate premium from weekly income and variance multiplier."""
    _ = risk_preference  # Retained for API compatibility.
    base = income * 0.006
    variance_multiplier = 1 + (max(0.0, income_variance) * 0.02)
    return round(base * variance_multiplier, 2)
