from __future__ import annotations

from unittest.mock import patch

import numpy as np

from app.premium_utils import calculate_pricing_details
from ml.feature_engineering import build_features, summarize_forecast
from ml.predict import explain_prediction, get_next_week_risk_score, get_risk_score


class DummyRiskModel:
    n_features_in_ = 9

    def _score(self, rows):
        values = np.asarray(rows, dtype=float)
        avg_temp = values[:, 0] / 50.0
        total_rain = values[:, 2] / 300.0
        trigger_days = values[:, 4] / 7.0
        avg_payout_pct = values[:, 5] / 100.0
        score = 0.4 * avg_temp + 0.3 * total_rain + 0.2 * trigger_days + 0.1 * avg_payout_pct
        return np.clip(score, 0.0, 1.0)

    def predict(self, rows):
        score = self._score(rows)
        return (score >= 0.5).astype(int)

    def predict_proba(self, rows):
        score = self._score(rows)
        return np.column_stack([1.0 - score, score])


def _build_forecast(avg_temp: float, total_rain: float, trigger_days: int) -> list[dict]:
    forecast = []
    remaining_rain = total_rain
    for day in range(7):
        if day < trigger_days:
            rain = min(remaining_rain, total_rain / max(trigger_days, 1))
            temp = avg_temp
            remaining_rain -= rain
        else:
            rain = 0.0
            temp = max(20.0, avg_temp - 8.0)
        forecast.append({"date": f"2026-04-{day + 1:02d}", "temperature": temp, "rain": rain})
    return forecast


def test_feature_engineering_is_consistent():
    forecast = _build_forecast(avg_temp=42.0, total_rain=140.0, trigger_days=4)

    features = build_features(forecast)
    summary = summarize_forecast(forecast)

    assert len(features) == 9
    assert features[0] == summary["avg_temp"]
    assert features[2] == summary["total_rain"]
    assert features[4] == summary["trigger_days"]
    assert features[6] == summary["temp_variance"]
    assert features[8] == summary["consecutive_trigger_days"]


def test_explain_prediction_high_temp_and_rain():
    reasons = explain_prediction(
        {
            "avg_temp": 45.0,
            "max_temp": 49.0,
            "total_rain": 180.0,
            "max_rain": 60.0,
            "trigger_days": 5,
            "avg_payout_pct": 70.0,
            "temp_variance": 8.0,
            "rain_variance": 25.0,
            "consecutive_trigger_days": 3,
        }
    )

    assert "High temperature" in reasons
    assert "Heavy rainfall" in reasons
    assert "Frequent disruptions" in reasons


def test_next_week_risk_uses_model_for_high_and_low_forecasts():
    high_forecast = _build_forecast(avg_temp=47.0, total_rain=210.0, trigger_days=6)
    low_forecast = _build_forecast(avg_temp=24.0, total_rain=5.0, trigger_days=0)

    with patch("ml.predict._risk_model", DummyRiskModel()):
        high_result = get_next_week_risk_score(high_forecast)
        low_result = get_next_week_risk_score(low_forecast)

    assert high_result["ml_used"] is True
    assert low_result["ml_used"] is True
    assert high_result["risk_score"] > low_result["risk_score"]
    assert high_result["risk_score"] > 0.6
    assert low_result["risk_score"] < 0.4


def test_next_week_risk_falls_back_when_model_missing():
    forecast = _build_forecast(avg_temp=39.0, total_rain=90.0, trigger_days=2)

    with patch("ml.predict._risk_model", None), patch("ml.predict._load_model", return_value=None):
        result = get_next_week_risk_score(forecast)

    assert result["ml_used"] is False
    assert 0.0 <= result["risk_score"] <= 1.0
    assert isinstance(result["explanation"], list)


def test_calibrated_risk_probability_distribution_ranges():
    clear_weather = [
        {"temperature": 27.0, "rain": 0.0, "aqi": 35.0},
        {"temperature": 28.0, "rain": 0.0, "aqi": 40.0},
        {"temperature": 27.0, "rain": 0.0, "aqi": 38.0},
        {"temperature": 28.0, "rain": 1.0, "aqi": 42.0},
        {"temperature": 29.0, "rain": 0.0, "aqi": 45.0},
        {"temperature": 28.0, "rain": 0.0, "aqi": 39.0},
        {"temperature": 27.0, "rain": 0.0, "aqi": 36.0},
    ]
    moderate_rain = [
        {"temperature": 33.0, "rain": 18.0, "aqi": 80.0},
        {"temperature": 34.0, "rain": 22.0, "aqi": 85.0},
        {"temperature": 32.0, "rain": 15.0, "aqi": 90.0},
        {"temperature": 35.0, "rain": 20.0, "aqi": 88.0},
        {"temperature": 34.0, "rain": 25.0, "aqi": 92.0},
        {"temperature": 33.0, "rain": 18.0, "aqi": 86.0},
        {"temperature": 32.0, "rain": 12.0, "aqi": 84.0},
    ]
    heavy_rain_heatwave = [
        {"temperature": 43.0, "rain": 60.0, "aqi": 170.0},
        {"temperature": 44.0, "rain": 75.0, "aqi": 190.0},
        {"temperature": 45.0, "rain": 80.0, "aqi": 200.0},
        {"temperature": 42.0, "rain": 65.0, "aqi": 180.0},
        {"temperature": 46.0, "rain": 90.0, "aqi": 210.0},
        {"temperature": 44.0, "rain": 70.0, "aqi": 195.0},
        {"temperature": 43.0, "rain": 85.0, "aqi": 205.0},
    ]

    clear_prob = get_risk_score({"forecast_data": clear_weather})
    moderate_prob = get_risk_score({"forecast_data": moderate_rain})
    heavy_prob = get_risk_score({"forecast_data": heavy_rain_heatwave})

    assert 0.05 <= clear_prob <= 0.10
    assert 0.12 <= moderate_prob <= 0.20
    assert 0.18 <= heavy_prob <= 0.30
    assert clear_prob < moderate_prob < heavy_prob


def test_risk_score_changes_premium_and_coverage_outputs():
    clear_weather = [{"temperature": 27.0, "rain": 0.0, "aqi": 35.0} for _ in range(7)]
    heavy_rain_heatwave = [{"temperature": 45.0, "rain": 80.0, "aqi": 200.0} for _ in range(7)]

    clear_pricing = calculate_pricing_details(income=500.0, forecast_data=clear_weather)
    heavy_pricing = calculate_pricing_details(income=500.0, forecast_data=heavy_rain_heatwave)

    assert heavy_pricing["premium"] >= clear_pricing["premium"]
    assert heavy_pricing["coverage"] <= clear_pricing["coverage"]
