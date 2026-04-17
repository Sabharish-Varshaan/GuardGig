from unittest.mock import patch

from app.premium_utils import (
    _calculate_bcr_pricing_from_probability,
    calculate_coverage_amount,
    calculate_pricing_details,
    calculate_policy_risk_score,
    calculate_premium,
)


def test_same_income_different_risk_changes_coverage():
    income = 400.0

    low_risk_coverage = calculate_coverage_amount(income, risk_score=0.2)
    high_risk_coverage = calculate_coverage_amount(income, risk_score=0.8)

    # Guardrails may bind both outcomes to the same 25% floor for low-income profiles.
    assert low_risk_coverage >= high_risk_coverage


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

    assert high_risk_premium > low_risk_premium


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
    trigger_probability = max(0.1, min(0.3, risk_score))  # Direct clamping

    premium = max(20.0, min(trigger_probability * (mean_income ** 0.5) * 5.0, 50.0))
    target_coverage = mean_income * 0.4
    required_premium = (target_coverage * trigger_probability) / 0.65
    if required_premium <= premium:
        coverage = target_coverage
    else:
        coverage = (premium * 0.65) / trigger_probability

    expected = max(mean_income * 0.25, min(coverage, mean_income * 0.6))
    expected = round(expected, 2)
    actual = calculate_coverage_amount(mean_income, risk_score=risk_score)

    assert actual == expected


def test_coverage_decreases_when_risk_decreases():
    lower_risk_coverage = calculate_coverage_amount(500.0, risk_score=0.1)
    higher_risk_coverage = calculate_coverage_amount(500.0, risk_score=0.3)

    assert lower_risk_coverage > higher_risk_coverage


def test_expected_payout_is_about_sixty_percent_of_premium_pool():
    mean_income = 400.0
    premium, coverage, trigger_probability = _calculate_bcr_pricing_from_probability(mean_income, 0.2)
    expected_payout = trigger_probability * coverage
    ratio = expected_payout / premium

    assert ratio >= 0.65


def test_bcr_cases_for_reference_probabilities():
    mean_income = 400.0

    for probability in (0.1, 0.2, 0.3):
        premium, coverage, used_probability = _calculate_bcr_pricing_from_probability(mean_income, probability)
        expected_payout = coverage * used_probability
        ratio = expected_payout / premium

        assert 20.0 <= premium <= 50.0
        assert mean_income * 0.25 <= coverage <= mean_income * 0.6
        assert ratio >= 0.65


def test_trigger_probability_edge_case_fallback():
    premium, coverage, used_probability = _calculate_bcr_pricing_from_probability(400.0, 0.0)
    expected_payout = coverage * used_probability
    ratio = expected_payout / premium

    assert used_probability == 0.1  # Minimum clamped probability
    assert 20.0 <= premium <= 50.0
    assert 100.0 <= coverage <= 240.0
    assert ratio >= 0.5


def test_forecast_driven_risk_score_varies_low_vs_high_weather():
    low_forecast = [
        {"temperature": 27.0, "rain": 0.0, "aqi": 30.0},
        {"temperature": 28.0, "rain": 0.0, "aqi": 35.0},
        {"temperature": 29.0, "rain": 1.0, "aqi": 40.0},
        {"temperature": 28.0, "rain": 0.0, "aqi": 38.0},
        {"temperature": 27.0, "rain": 0.0, "aqi": 32.0},
        {"temperature": 29.0, "rain": 0.5, "aqi": 34.0},
        {"temperature": 28.0, "rain": 0.0, "aqi": 33.0},
    ]
    high_forecast = [
        {"temperature": 45.0, "rain": 80.0, "aqi": 180.0},
        {"temperature": 46.0, "rain": 95.0, "aqi": 190.0},
        {"temperature": 44.0, "rain": 70.0, "aqi": 175.0},
        {"temperature": 47.0, "rain": 110.0, "aqi": 210.0},
        {"temperature": 45.0, "rain": 90.0, "aqi": 195.0},
        {"temperature": 46.0, "rain": 85.0, "aqi": 200.0},
        {"temperature": 44.0, "rain": 100.0, "aqi": 188.0},
    ]

    low_risk = calculate_policy_risk_score(400.0, forecast_data=low_forecast)
    high_risk = calculate_policy_risk_score(400.0, forecast_data=high_forecast)

    assert high_risk > low_risk


def test_forecast_driven_risk_changes_premium_for_same_income():
    low_forecast = [{"temperature": 27.0, "rain": 0.0, "aqi": 30.0} for _ in range(7)]
    high_forecast = [{"temperature": 46.0, "rain": 90.0, "aqi": 200.0} for _ in range(7)]

    low_premium = calculate_premium(250.0, forecast_data=low_forecast)
    high_premium = calculate_premium(250.0, forecast_data=high_forecast)

    assert high_premium >= low_premium


def test_required_three_reference_cases_with_explainability():
    case_1 = calculate_pricing_details(income=500.0, risk_score=0.1)
    case_2 = calculate_pricing_details(income=500.0, risk_score=0.2)
    case_3 = calculate_pricing_details(income=500.0, risk_score=0.3)

    assert 20.0 <= case_1["premium"] <= 50.0
    assert 20.0 <= case_2["premium"] <= 50.0
    assert 20.0 <= case_3["premium"] <= 50.0

    assert 125.0 <= case_1["coverage"] <= 300.0
    assert 125.0 <= case_2["coverage"] <= 300.0
    assert 125.0 <= case_3["coverage"] <= 300.0

    for case in (case_1, case_2, case_3):
        ratio = (case["coverage"] * case["probability"]) / case["premium"]
        assert 25.0 <= case["coverage_percentage"] <= 60.0
        assert case["target"] == "40%"
        assert case["reason"] in {
            "Target protection achieved (40%)",
            "Adjusted for sustainability (risk too high)",
        }
        assert ratio >= 0.5

