"""Load trained models and expose prediction helpers.

Functions:
 - get_risk_score(features: dict) -> float
 - get_fraud_score(features: dict) -> float

Both functions will try to load the saved model artifacts from the same folder
and fall back to safe heuristics when models are missing.
"""
from __future__ import annotations

from pathlib import Path
import logging
from typing import Dict, Any

import joblib
import numpy as np

_HERE = Path(__file__).resolve().parent
_RISK_MODEL_PATH = _HERE / "risk_model.pkl"
_FRAUD_MODEL_PATH = _HERE / "fraud_model.pkl"

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
        if _risk_model is not None:
            proba = _risk_model.predict_proba([vec])[0][1]
            return float(np.clip(proba, 0.0, 1.0))
    except Exception as exc:
        logger.debug("Risk model prediction failed: %s", exc)

    # fallback heuristic: higher income -> lower risk, higher variance/rain/aqi -> higher risk
    income_norm, variance_norm, rain_norm, aqi_norm = vec
    score = 0.5 * (1.0 - min(1.0, income_norm / 3.0))
    score += 0.3 * min(1.0, variance_norm)
    score += 0.1 * min(1.0, rain_norm)
    score += 0.1 * min(1.0, aqi_norm)
    return float(max(0.0, min(1.0, round(score, 2))))


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
