from unittest.mock import patch

from app.premium_utils import calculate_premium


def test_low_income_low_risk_maps_to_floor_premium():
    with patch("app.premium_utils.calculate_policy_risk_score", return_value=0.2):
        premium = calculate_premium(100.0, "Low", income_variance=0.0)

    assert premium == 20.0


def test_high_income_high_risk_maps_to_cap_premium():
    with patch("app.premium_utils.calculate_policy_risk_score", return_value=0.8):
        premium = calculate_premium(2000.0, "High", income_variance=0.0)

    assert premium == 50.0


def test_premium_always_within_allowed_range():
    with patch("app.premium_utils.calculate_policy_risk_score", return_value=0.5):
        very_low = calculate_premium(10.0, "Medium", income_variance=0.0)
        mid = calculate_premium(100.0, "Medium", income_variance=0.0)
        very_high = calculate_premium(10000.0, "Medium", income_variance=0.0)

    assert 20.0 <= very_low <= 50.0
    assert 20.0 <= mid <= 50.0
    assert 20.0 <= very_high <= 50.0
