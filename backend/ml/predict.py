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
_FRAUD_SPOT_CHECK_KM = 5.0

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


def _coerce_forecast_rows(payload: Dict[str, Any]) -> list[dict[str, float]]:
    forecast_data = payload.get("forecast_data")
    if isinstance(forecast_data, list):
        return [row for row in forecast_data if isinstance(row, dict)]

    row = {
        "temperature": float(payload.get("temperature") or payload.get("temp") or 0.0),
        "rain": float(payload.get("rain") or payload.get("rain_mm") or 0.0),
        "aqi": float(payload.get("aqi") or 0.0),
    }
    return [row]


def _features_for_risk(payload: Dict[str, Any]) -> list[float]:
    forecast_rows = _coerce_forecast_rows(payload)
    return build_features(forecast_rows)


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
    elif hasattr(model, "decision_function"):
        decision = float(model.decision_function([vec])[0])
        raw = 1.0 / (1.0 + np.exp(-decision))
    else:
        raw = float(model.predict([vec])[0])
    return float(np.clip(raw, 0.0, 1.0))


def _post_process_risk_probability(raw_prob: float) -> float:
    scaled = 0.05 + (float(raw_prob) * 0.25)
    return float(np.clip(scaled, 0.05, 0.30))


def _load_risk_model(force_refresh: bool = False):
    global _risk_model

    if force_refresh or _risk_model is None:
        _risk_model = _load_model(_RISK_MODEL_PATH)

    return _risk_model


def _risk_model_is_compatible(model: Any) -> bool:
    if model is None:
        return False

    if not hasattr(model, "predict_proba"):
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
    location_change = float(payload.get("location_change") or payload.get("location_change_km") or 0.0)
    activity_status = str(payload.get("activity_status") or "unknown").lower()

    claims_norm = claims_today / 5.0
    time_norm = 1.0 / (time_since_last + 1.0)
    location_flag = 1.0 if location_change > 0.5 else 0.0
    activity_flag = 1.0 if activity_status in {"inactive", "none", "no_activity", "suspicious"} else 0.0

    return [claims_norm, time_norm, location_flag, activity_flag]


def _fraud_safety_overlay(payload: Dict[str, Any]) -> float:
    claims_today = max(0.0, float(payload.get("number_of_claims_today") or 0.0))
    claim_frequency = max(claims_today, float(payload.get("claim_frequency") or 0.0))
    time_since_last = max(0.0, float(payload.get("time_since_last_claim") or 0.0))
    location_change_km = max(
        0.0,
        float(
            payload.get("location_change_km")
            or payload.get("gps_jump_km")
            or payload.get("location_change")
            or 0.0
        ),
    )
    activity_status = str(payload.get("activity_status") or "unknown").lower()

    reported_rain = payload.get("reported_rain_mm")
    actual_rain = payload.get("actual_rain_mm")
    weather_mismatch = bool(payload.get("weather_mismatch") or False)
    rain_gap = 0.0
    if reported_rain is not None and actual_rain is not None:
        rain_gap = abs(float(reported_rain) - float(actual_rain))
        weather_mismatch = weather_mismatch or rain_gap > 5.0

    score = 0.0

    if claim_frequency >= 8:
        score += 0.35
    elif claim_frequency >= 5:
        score += 0.25
    elif claim_frequency >= 3:
        score += 0.15
    elif claim_frequency >= 1:
        score += 0.05

    if time_since_last < 6:
        score += 0.15
    elif time_since_last < 24:
        score += 0.08

    if location_change_km > 20:
        score += 0.40
    elif location_change_km > _FRAUD_SPOT_CHECK_KM:
        score += 0.30
    elif location_change_km > 1.0:
        score += 0.12

    if weather_mismatch:
        score += 0.25 if rain_gap > 20.0 else 0.15

    if activity_status in {"inactive", "none", "no_activity", "suspicious"}:
        score += 0.35

    if payload.get("location_valid") is False:
        score += 0.25

    if bool(payload.get("gps_spoofing_suspected")):
        score += 0.30

    return float(np.clip(score, 0.0, 1.0))


def get_risk_score(features: Dict[str, Any]) -> float:
    """Return risk score in [0,1].

    Pricing risk uses the same 9-feature forecast representation as admin forecasting.
    """
    forecast_rows = _coerce_forecast_rows(features)
    summary = summarize_forecast(forecast_rows)
    vec = _features_for_risk(features)

    # Ensure we have the calibrated probability model, not a legacy regressor.
    ensure_risk_model_available()
    model = _load_risk_model()

    try:
        if _is_model_compatible(model, len(vec)):
            raw_prob = _predict_probability(model, vec)
            prob = _post_process_risk_probability(raw_prob)
            print("[ML PROBABILITY]", {"raw_prob": round(raw_prob, 4), "final_prob": round(prob, 4)})
            logger.info(
                "[ML PRICING USED] feature_count=%s raw_prob=%.4f calibrated_prob=%.4f",
                len(vec),
                raw_prob,
                prob,
            )
            return prob

        logger.warning(
            "[ML PRICING FALLBACK] model_incompatible=True expected=%s got=%s",
            getattr(model, "n_features_in_", "unknown"),
            len(vec),
        )
    except Exception as exc:
        logger.warning("[ML PRICING FALLBACK] prediction_failed=%s", exc)

    raw_prob = float(np.clip(_next_week_heuristic(summary), 0.0, 1.0))
    prob = _post_process_risk_probability(raw_prob)
    print("[ML PROBABILITY]", {"raw_prob": round(raw_prob, 4), "final_prob": round(prob, 4)})
    return prob


def get_next_week_risk_score(forecast_data) -> dict:
    """Return the explainable next-week risk payload for admin forecasts."""
    summary = summarize_forecast(forecast_data)
    features = build_features(forecast_data)
    explanation = explain_prediction(summary)

    model = _load_risk_model()
    if _risk_model_is_compatible(model):
        try:
            score = _predict_probability(model, features)
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
    Optional safety inputs: location_change_km, claim_frequency, reported_rain_mm, actual_rain_mm,
    weather_mismatch, gps_spoofing_suspected, location_valid.
    """
    vec = _features_for_fraud(features)
    safety_overlay = _fraud_safety_overlay(features)
    try:
        if _fraud_model is not None and _is_model_compatible(_fraud_model, len(vec)):
            proba = float(_fraud_model.predict_proba([vec])[0][1])
            return float(np.clip(max(proba, safety_overlay), 0.0, 1.0))
    except Exception as exc:
        logger.debug("Fraud model prediction failed: %s", exc)

    # conservative fallback heuristic when the saved model is missing or incompatible
    claims_norm, time_norm, location_flag, activity_flag = vec
    score = (
        0.22 * claims_norm
        + 0.18 * (1.0 - time_norm)
        + 0.20 * location_flag
        + 0.20 * activity_flag
        + 0.20 * safety_overlay
    )
    score = max(score, safety_overlay)
    score = min(1.0, round(score, 2))
    return float(score)


if __name__ == "__main__":
    print("ML predict helpers. Models present:", _RISK_MODEL_PATH.exists(), _FRAUD_MODEL_PATH.exists())
