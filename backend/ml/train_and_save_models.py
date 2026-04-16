"""Train synthetic ML models and save them as pickles.

This script trains:
 - LogisticRegression risk model for admin next-week forecasting (6 features)
 - RandomForestClassifier fraud model (4 features)

Run this script locally to generate `risk_model.pkl` and `fraud_model.pkl`.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import joblib


def generate_risk_data(n=3000, random_state=1):
    rng = np.random.RandomState(random_state)
    avg_temp = rng.uniform(20.0, 42.0, size=(n, 1))
    max_temp = np.maximum(avg_temp, rng.uniform(28.0, 50.0, size=(n, 1)))
    total_rain = np.clip(rng.gamma(shape=1.8, scale=70.0, size=(n, 1)), 0.0, 900.0)
    max_rain = np.clip(total_rain * rng.uniform(0.1, 0.65, size=(n, 1)), 0.0, 220.0)

    heat_severity = np.clip((max_temp - 35.0) / 15.0, 0.0, 1.0)
    rain_severity = np.clip(total_rain / 700.0, 0.0, 1.0)
    blended_severity = 0.55 * rain_severity + 0.45 * heat_severity

    trigger_days = np.clip(np.round(blended_severity * 7.0 + rng.normal(0.0, 1.0, size=(n, 1))), 0.0, 7.0)
    avg_payout_pct = np.clip((0.6 * rain_severity + 0.4 * heat_severity) * 100.0 + rng.normal(0.0, 8.0, size=(n, 1)), 0.0, 100.0)

    # Normalize exactly as inference does.
    X = np.hstack([
        np.clip(avg_temp / 50.0, 0.0, 1.5),
        np.clip(max_temp / 55.0, 0.0, 1.5),
        np.clip(total_rain / 700.0, 0.0, 2.0),
        np.clip(max_rain / 200.0, 0.0, 2.0),
        np.clip(trigger_days / 7.0, 0.0, 1.0),
        np.clip(avg_payout_pct / 100.0, 0.0, 1.0),
    ])

    risk_cont = (
        0.15 * X[:, 0]
        + 0.15 * X[:, 1]
        + 0.20 * np.clip(X[:, 2], 0.0, 1.0)
        + 0.20 * np.clip(X[:, 3], 0.0, 1.0)
        + 0.15 * X[:, 4]
        + 0.15 * X[:, 5]
    )
    # add noise and threshold to create binary labels
    prob = 1.0 / (1.0 + np.exp(-5 * (risk_cont - 0.4)))
    y = (prob + rng.normal(scale=0.05, size=prob.shape) > 0.5).astype(int)
    return X, y


def generate_fraud_data(n=2000, random_state=2):
    rng = np.random.RandomState(random_state)
    # number_of_claims_today [0,5], time_since_last_claim [0,100], location_change [0,2], activity_flag
    claims = rng.poisson(0.4, size=(n, 1))
    time_since = rng.exponential(scale=10.0, size=(n, 1))
    loc_change = rng.uniform(0.0, 2.0, size=(n, 1))
    activity = rng.choice([0, 1], size=(n, 1), p=[0.85, 0.15])  # 1 means inactive/suspicious

    X = np.hstack([claims / 5.0, 1.0 / (time_since + 1.0), (loc_change > 0.5).astype(float), activity.astype(float)])

    # fraud proxy
    fraud_cont = 0.4 * (claims.flatten() / 5.0) + 0.35 * activity.flatten() + 0.2 * (loc_change.flatten() > 0.5) + 0.05 * (1 - (1.0 / (time_since.flatten() + 1.0)))
    prob = np.clip(fraud_cont + rng.normal(scale=0.05, size=fraud_cont.shape), 0.0, 1.0)
    y = (prob > 0.5).astype(int)
    return X, y


def train_and_save(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    X_risk, y_risk = generate_risk_data()
    risk_model = LogisticRegression(max_iter=1000)
    risk_model.fit(X_risk, y_risk)

    X_fraud, y_fraud = generate_fraud_data()
    fraud_model = RandomForestClassifier(n_estimators=100, random_state=42)
    fraud_model.fit(X_fraud, y_fraud)

    joblib.dump(risk_model, output_dir / "risk_model.pkl")
    joblib.dump(fraud_model, output_dir / "fraud_model.pkl")
    print("Saved models to", output_dir)


if __name__ == "__main__":
    train_and_save(Path(__file__).resolve().parent)
