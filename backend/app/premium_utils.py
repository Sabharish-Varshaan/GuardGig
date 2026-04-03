from typing import Literal

RiskPreference = Literal["Low", "Medium", "High"]

_RISK_FACTOR_BY_PREFERENCE: dict[RiskPreference, float] = {
    "Low": 0.02,
    "Medium": 0.05,
    "High": 0.08,
}


def calculate_premium(income: float, risk_preference: str = "Medium", income_variance: float = 0.0) -> float:
    """Calculate premium using base 0.6% of income plus a small risk factor."""
    normalized = risk_preference.title()
    if normalized not in _RISK_FACTOR_BY_PREFERENCE:
        normalized = "Medium"

    base = income * 0.006
    risk_add_on = base * _RISK_FACTOR_BY_PREFERENCE[normalized]  # type: ignore[index]
    base_premium = base + risk_add_on
    variance_multiplier = 1 + (max(0.0, income_variance) * 0.02)
    return round(base_premium * variance_multiplier, 2)
