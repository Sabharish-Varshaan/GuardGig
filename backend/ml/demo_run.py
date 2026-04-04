"""Small local demo to call the ML helpers and print scores.

Run this from the backend folder with your virtualenv activated:

    python .\ml\demo_run.py

It prints whether model pickles exist and sample risk/fraud scores.
"""
from pprint import pprint

from pathlib import Path

try:
    from ml.predict import get_risk_score, get_fraud_score, _RISK_MODEL_PATH, _FRAUD_MODEL_PATH
except Exception as exc:
    print("Failed to import ml.predict:", exc)
    raise


def run_demo():
    print("risk model exists:", _RISK_MODEL_PATH.exists())
    print("fraud model exists:", _FRAUD_MODEL_PATH.exists())

    risk_features = {
        "mean_income": 100.0,  # daily mean income (example)
        "income_variance": 0.2,
        "rain": 50.0,
        "aqi": 120.0,
        "lat": 13.0,
        "lon": 80.0,
    }

    fraud_features = {
        "number_of_claims_today": 1,
        "time_since_last_claim": 48.0,
        "location_change": 0.2,
        "activity_status": "active",
    }

    print("\nSample risk features:")
    pprint(risk_features)
    rs = get_risk_score(risk_features)
    print(f"risk_score: {rs:.3f}")

    print("\nSample fraud features:")
    pprint(fraud_features)
    fs = get_fraud_score(fraud_features)
    print(f"fraud_score: {fs:.3f}")


if __name__ == "__main__":
    run_demo()
