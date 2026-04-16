from __future__ import annotations

from unittest.mock import patch

import numpy as np

from ml.feature_engineering import build_features, summarize_forecast
from ml.predict import explain_prediction, get_next_week_risk_score


class DummyRiskModel:
    n_features_in_ = 9

    def predict(self, rows):
        values = np.asarray(rows, dtype=float)
        avg_temp = values[:, 0] / 50.0
        total_rain = values[:, 2] / 300.0
        trigger_days = values[:, 4] / 7.0
        avg_payout_pct = values[:, 5] / 100.0
        score = 0.4 * avg_temp + 0.3 * total_rain + 0.2 * trigger_days + 0.1 * avg_payout_pct
        return np.clip(score, 0.0, 1.0)


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
