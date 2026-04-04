"""Train simple synthetic ML models and save them as pickles.

This script trains:
 - LogisticRegression risk model (4 features)
 - RandomForestClassifier fraud model (4 features)

Run this script locally to generate `risk_model.pkl` and `fraud_model.pkl`.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import joblib


def generate_risk_data(n=2000, random_state=1):
    rng = np.random.RandomState(random_state)
    # income_norm in [0.0, 3.0], variance [0,1], rain_norm [0,1], aqi_norm [0,1]
    income = rng.uniform(0.1, 3.0, size=(n, 1))
    variance = rng.beta(2, 5, size=(n, 1))
    rain = rng.exponential(scale=0.2, size=(n, 1))
    aqi = rng.beta(2, 8, size=(n, 1))

    X = np.hstack([income, variance, rain, aqi])

    # continuous risk proxy: higher variance/rain/aqi and lower income -> higher risk
    risk_cont = 0.6 * (1 - (income.flatten() / 3.0)) + 0.2 * variance.flatten() + 0.1 * np.minimum(1.0, rain.flatten()) + 0.1 * aqi.flatten()
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
