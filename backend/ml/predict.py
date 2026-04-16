"""Load trained models and expose prediction helpers.

Functions:
 - get_risk_score(features: dict) -> float
 - get_fraud_score(features: dict) -> float

Both functions will try to load the saved model artifacts from the same folder
and fall back to safe heuristics when models are missing.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

import joblib
import numpy as np

from .feature_engineering import build_features, summarize_forecast

_HERE = Path(__file__).resolve().parent
_RISK_MODEL_PATH = _HERE / "risk_model.pkl"
_FRAUD_MODEL_PATH = _HERE / "fraud_model.pkl"
_EXPECTED_RISK_FEATURES = 9

logger = logging.getLogger(__name__)


def _load_model(path: Path):
    try:
        return joblib.load(path)
    except Exception as exc:
        logger.debug("Failed to load model %s: %s", path, exc)
        return None


# load lazily
_risk_model = _load_model(_RISK_MODEL_PATH)
_fraud_model = _load_model(_FRAUD_MODEL_PATH)


def _features_for_risk(payload: Dict[str, Any]) -> list[float]:
    # Expecting keys: mean_income, income_variance, rain, aqi, lat, lon
    mean_income = float(payload.get("mean_income") or 0.0)
    income_variance = float(payload.get("income_variance") or 0.0)
    rain = float(payload.get("rain") or 0.0)
    aqi = float(payload.get("aqi") or 0.0)

    # Feature engineering per spec
    income_norm = mean_income / 1000.0
    variance_norm = income_variance
    rain_norm = rain / 100.0
    aqi_norm = aqi / 500.0

    return [income_norm, variance_norm, rain_norm, aqi_norm]


def _features_for_next_week_risk(payload: Dict[str, Any]) -> list[float]:
    """Build normalized 6-feature vector for admin next-week city forecasting.

    Expected payload keys:
    - avg_temperature
    - max_temperature
    - total_rainfall
    - max_rainfall
    - trigger_days
    - avg_payout_percentage
    """
    avg_temperature = float(payload.get("avg_temperature") or 0.0)
    max_temperature = float(payload.get("max_temperature") or 0.0)
    total_rainfall = float(payload.get("total_rainfall") or 0.0)
    max_rainfall = float(payload.get("max_rainfall") or 0.0)
    trigger_days = float(payload.get("trigger_days") or 0.0)
    avg_payout_percentage = float(payload.get("avg_payout_percentage") or 0.0)

    # Keep normalization deterministic and aligned with training script.
    avg_temp_norm = np.clip(avg_temperature / 50.0, 0.0, 1.5)
    max_temp_norm = np.clip(max_temperature / 55.0, 0.0, 1.5)
    total_rain_norm = np.clip(total_rainfall / 700.0, 0.0, 2.0)
    max_rain_norm = np.clip(max_rainfall / 200.0, 0.0, 2.0)
    trigger_days_norm = np.clip(trigger_days / 7.0, 0.0, 1.0)
    avg_payout_norm = np.clip(avg_payout_percentage / 100.0, 0.0, 1.0)

    return [
        float(avg_temp_norm),
        float(max_temp_norm),
        float(total_rain_norm),
        float(max_rain_norm),
        float(trigger_days_norm),
        float(avg_payout_norm),
    ]


def _is_model_compatible(model: Any, expected_features: int) -> bool:
    if model is None:
        return False
    n_features = getattr(model, "n_features_in_", None)
    if n_features is None:
        return True
    return int(n_features) == int(expected_features)


def _predict_probability(model: Any, vec: list[float]) -> float:
    if hasattr(model, "predict_proba"):
        raw = float(model.predict_proba([vec])[0][1])
    else:
        raw = float(model.predict([vec])[0])
    return float(np.clip(raw, 0.0, 1.0))


def _load_risk_model(force_refresh: bool = False):
    global _risk_model

    if force_refresh or _risk_model is None:
        _risk_model = _load_model(_RISK_MODEL_PATH)

    return _risk_model


def _risk_model_is_compatible(model: Any) -> bool:
    if model is None:
        return False

    n_features = getattr(model, "n_features_in_", None)
    if n_features is None:
        return True

    return int(n_features) == _EXPECTED_RISK_FEATURES


def ensure_risk_model_available(force_refresh: bool = False) -> bool:
    """Ensure the upgraded risk model exists and matches the new feature set."""
    model = _load_risk_model(force_refresh=force_refresh)
    if _risk_model_is_compatible(model):
        return True

    from .train_risk_model import train_risk_model

    train_risk_model()
    _load_risk_model(force_refresh=True)
    return _risk_model_is_compatible(_risk_model)


def explain_prediction(features: Dict[str, Any] | list[float]) -> list[str]:
    if isinstance(features, dict):
        summary = {
            "avg_temp": float(features.get("avg_temp", 0.0) or 0.0),
            "max_temp": float(features.get("max_temp", 0.0) or 0.0),
            "total_rain": float(features.get("total_rain", 0.0) or 0.0),
            "max_rain": float(features.get("max_rain", 0.0) or 0.0),
            "trigger_days": float(features.get("trigger_days", 0.0) or 0.0),
            "avg_payout_pct": float(features.get("avg_payout_pct", 0.0) or 0.0),
            "temp_variance": float(features.get("temp_variance", 0.0) or 0.0),
            "rain_variance": float(features.get("rain_variance", 0.0) or 0.0),
            "consecutive_trigger_days": float(features.get("consecutive_trigger_days", 0.0) or 0.0),
        }
    else:
        values = list(features or [])
        summary = {
            "avg_temp": float(values[0] if len(values) > 0 else 0.0),
            "max_temp": float(values[1] if len(values) > 1 else 0.0),
            "total_rain": float(values[2] if len(values) > 2 else 0.0),
            "max_rain": float(values[3] if len(values) > 3 else 0.0),
            "trigger_days": float(values[4] if len(values) > 4 else 0.0),
            "avg_payout_pct": float(values[5] if len(values) > 5 else 0.0),
            "temp_variance": float(values[6] if len(values) > 6 else 0.0),
            "rain_variance": float(values[7] if len(values) > 7 else 0.0),
            "consecutive_trigger_days": float(values[8] if len(values) > 8 else 0.0),
        }

    reasons: list[str] = []
    if summary["avg_temp"] > 40 or summary["max_temp"] > 45:
        reasons.append("High temperature")
    if summary["total_rain"] > 100 or summary["max_rain"] > 50:
        reasons.append("Heavy rainfall")
    if summary["trigger_days"] > 3:
        reasons.append("Frequent disruptions")
    if summary["consecutive_trigger_days"] >= 3:
        reasons.append("Persistent trigger streak")
    if summary["temp_variance"] > 6:
        reasons.append("Temperature volatility")
    if summary["rain_variance"] > 20:
        reasons.append("Rainfall volatility")

    return reasons[:4]


def _next_week_heuristic(summary: Dict[str, float]) -> float:
    avg_temp = summary["avg_temp"] / 50.0
    max_temp = summary["max_temp"] / 55.0
    total_rain = summary["total_rain"] / 300.0
    max_rain = summary["max_rain"] / 150.0
    trigger_days = summary["trigger_days"] / 7.0
    avg_payout_pct = summary["avg_payout_pct"] / 100.0
    temp_variance = summary["temp_variance"] / 10.0
    rain_variance = summary["rain_variance"] / 50.0
    consecutive_trigger_days = summary["consecutive_trigger_days"] / 7.0

    heuristic = (
        0.22 * avg_temp
        + 0.12 * max_temp
        + 0.20 * total_rain
        + 0.06 * max_rain
        + 0.14 * trigger_days
        + 0.10 * avg_payout_pct
        + 0.06 * temp_variance
        + 0.04 * rain_variance
        + 0.06 * consecutive_trigger_days
    )
    return float(np.clip(heuristic, 0.0, 1.0))


def _features_for_fraud(payload: Dict[str, Any]) -> list[float]:
    # Expecting keys: number_of_claims_today, time_since_last_claim, location_change, activity_status
    claims_today = float(payload.get("number_of_claims_today") or 0.0)
    time_since_last = float(payload.get("time_since_last_claim") or 0.0)
    location_change = float(payload.get("location_change") or 0.0)
    activity_status = str(payload.get("activity_status") or "unknown").lower()

    claims_norm = claims_today / 5.0
    time_norm = 1.0 / (time_since_last + 1.0)
    location_flag = 1.0 if location_change > 0.5 else 0.0
    activity_flag = 1.0 if activity_status in {"inactive", "none", "no_activity", "suspicious"} else 0.0

    return [claims_norm, time_norm, location_flag, activity_flag]


def get_risk_score(features: Dict[str, Any]) -> float:
    """Return risk score in [0,1].

    Features (dict) should include at least mean_income and income_variance. Other keys
    (rain, aqi) are optional and default to 0.
    """
    vec = _features_for_risk(features)
    try:
        if _is_model_compatible(_risk_model, len(vec)):
            return _predict_probability(_risk_model, vec)
    except Exception as exc:
        logger.debug("Risk model prediction failed: %s", exc)

    # fallback heuristic: higher income -> lower risk, higher variance/rain/aqi -> higher risk
    income_norm, variance_norm, rain_norm, aqi_norm = vec
    score = 0.5 * (1.0 - min(1.0, income_norm / 3.0))
    score += 0.3 * min(1.0, variance_norm)
    score += 0.1 * min(1.0, rain_norm)
    score += 0.1 * min(1.0, aqi_norm)
    return float(max(0.0, min(1.0, round(score, 2))))


def get_next_week_risk_score(forecast_data) -> dict:
    """Return the explainable next-week risk payload for admin forecasts."""
    summary = summarize_forecast(forecast_data)
    features = build_features(forecast_data)
    explanation = explain_prediction(summary)

    model = _load_risk_model()
    if _risk_model_is_compatible(model):
        try:
            score = float(np.clip(model.predict([features])[0], 0.0, 1.0))
            return {
                "risk_score": score,
                "ml_used": True,
                "explanation": explanation,
                "features": summary,
            }
        except Exception as exc:
            logger.warning("Admin next-week risk model prediction failed: %s", exc)

    return {
        "risk_score": _next_week_heuristic(summary),
        "ml_used": False,
        "explanation": explanation,
        "features": summary,
    }


def get_fraud_score(features: Dict[str, Any]) -> float:
    """Return fraud score in [0,1].

    Features expected: number_of_claims_today, time_since_last_claim, location_change, activity_status
    """
    vec = _features_for_fraud(features)
    try:
        if _fraud_model is not None:
            proba = _fraud_model.predict_proba([vec])[0][1]
            return float(np.clip(proba, 0.0, 1.0))
    except Exception as exc:
        logger.debug("Fraud model prediction failed: %s", exc)

    # fallback heuristic similar to previous behavior
    claims_norm, time_norm, location_flag, activity_flag = vec
    score = min(1.0, round(0.3 * claims_norm + 0.4 * activity_flag + 0.2 * location_flag + 0.1 * (1 - time_norm), 2))
    return float(score)


if __name__ == "__main__":
    print("ML predict helpers. Models present:", _RISK_MODEL_PATH.exists(), _FRAUD_MODEL_PATH.exists())
