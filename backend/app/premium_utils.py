from typing import Literal

RiskPreference = Literal["Low", "Medium", "High"]

_RISK_FACTOR_BY_PREFERENCE: dict[RiskPreference, float] = {
    "Low": 0.02,
    "Medium": 0.05,
    "High": 0.08,
}


def calculate_premium(income: float, risk_preference: str = "Medium") -> float:
    """Calculate premium using base 0.6% of income plus a small risk factor."""
    normalized = risk_preference.title()
    if normalized not in _RISK_FACTOR_BY_PREFERENCE:
        normalized = "Medium"

    base = income * 0.006
    risk_add_on = base * _RISK_FACTOR_BY_PREFERENCE[normalized]  # type: ignore[index]
    return round(base + risk_add_on, 2)
