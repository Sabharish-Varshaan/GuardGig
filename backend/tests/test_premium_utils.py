from unittest.mock import patch

from app.premium_utils import calculate_coverage_amount, calculate_premium


def test_same_income_different_risk_changes_coverage():
    income = 200.0

    low_risk_coverage = calculate_coverage_amount(income, risk_score=0.2)
    high_risk_coverage = calculate_coverage_amount(income, risk_score=0.8)

    assert high_risk_coverage > low_risk_coverage


def test_same_risk_different_income_changes_coverage():
    risk_score = 0.5

    low_income_coverage = calculate_coverage_amount(120.0, risk_score=risk_score)
    high_income_coverage = calculate_coverage_amount(240.0, risk_score=risk_score)

    assert high_income_coverage > low_income_coverage


def test_premium_varies_with_ml_risk_for_same_income():
    income = 300.0
    with patch("app.premium_utils.calculate_policy_risk_score", side_effect=[0.25, 0.75]):
        low_risk_premium = calculate_premium(income, "Medium", income_variance=0.0)
        high_risk_premium = calculate_premium(income, "Medium", income_variance=0.0)

    assert high_risk_premium != low_risk_premium


def test_premium_soft_normalization_bounds():
    very_low = calculate_premium(10.0, "Medium", income_variance=0.0, risk_score=0.05)
    mid = calculate_premium(200.0, "Medium", income_variance=0.0, risk_score=0.5)
    very_high = calculate_premium(10000.0, "Medium", income_variance=0.0, risk_score=1.0)

    assert 20.0 <= very_low <= 50.0
    assert 20.0 <= mid <= 50.0
    assert 20.0 <= very_high <= 50.0


def test_mid_income_coverage_stays_reasonable():
    # Mid-income range should stay around sustainable coverage levels.
    mid_income = 500.0
    low_risk = calculate_coverage_amount(mid_income, risk_score=0.2)
    high_risk = calculate_coverage_amount(mid_income, risk_score=0.8)

    assert low_risk <= 1000.0
    assert high_risk <= 1000.0


def test_coverage_formula_matches_expected_expression():
    mean_income = 150.0
    risk_score = 0.4
    trigger_probability = 0.08 - (0.06 * risk_score)
    premium = max(20.0, min(trigger_probability * mean_income * 3.0, 50.0))
    expected = round((premium / trigger_probability) * 0.65, 2)
    actual = calculate_coverage_amount(mean_income, risk_score=risk_score)

    assert actual == expected


def test_coverage_decreases_when_risk_decreases():
    lower_risk_coverage = calculate_coverage_amount(500.0, risk_score=0.5)
    higher_risk_coverage = calculate_coverage_amount(500.0, risk_score=0.8)

    assert lower_risk_coverage < higher_risk_coverage


def test_expected_payout_is_about_sixty_percent_of_premium_pool():
    mean_income = 500.0
    risk_score = 0.8
    trigger_probability = 0.08 - (0.06 * risk_score)

    premium = calculate_premium(mean_income, "Medium", income_variance=0.0, risk_score=risk_score)
    coverage = calculate_coverage_amount(mean_income, risk_score=risk_score)
    expected_payout = trigger_probability * coverage
    ratio = expected_payout / premium

    assert 0.60 <= ratio <= 0.70

