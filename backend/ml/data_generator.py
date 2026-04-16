from __future__ import annotations

from dataclasses import dataclass

import numpy as np


FEATURE_NAMES = [
    "avg_temp",
    "max_temp",
    "total_rain",
    "max_rain",
    "trigger_days",
    "avg_payout_pct",
    "temp_variance",
    "rain_variance",
    "consecutive_trigger_days",
]


@dataclass(frozen=True)
class SyntheticRiskDataset:
    features: np.ndarray
    targets: np.ndarray
    feature_names: list[str]


def _clip(values: np.ndarray, lower: float, upper: float) -> np.ndarray:
    return np.clip(values, lower, upper)


def generate_synthetic_risk_dataset(n_samples: int = 3000, random_state: int = 42) -> SyntheticRiskDataset:
    rng = np.random.default_rng(random_state)

    avg_temp = rng.uniform(20.0, 50.0, size=n_samples)
    max_temp = _clip(avg_temp + rng.uniform(0.0, 8.0, size=n_samples), 25.0, 55.0)
    total_rain = rng.uniform(0.0, 300.0, size=n_samples)
    max_rain = _clip(total_rain * rng.uniform(0.15, 0.6, size=n_samples), 0.0, 150.0)

    trigger_pressure = (
        0.45 * _clip((avg_temp - 30.0) / 20.0, 0.0, 1.0)
        + 0.35 * _clip(total_rain / 300.0, 0.0, 1.0)
        + 0.20 * rng.uniform(0.0, 1.0, size=n_samples)
    )
    trigger_days = _clip(np.rint(trigger_pressure * 7.0), 0.0, 7.0)
    avg_payout_pct = _clip(
        0.55 * (total_rain / 300.0) * 100.0 + 0.45 * (avg_temp / 50.0) * 100.0 + rng.normal(0.0, 6.0, size=n_samples),
        0.0,
        100.0,
    )

    temp_variance = _clip(max_temp - avg_temp + rng.uniform(0.0, 2.0, size=n_samples), 0.0, 10.0)
    rain_variance = _clip(rng.uniform(0.0, 50.0, size=n_samples) * _clip(total_rain / 300.0, 0.0, 1.0), 0.0, 50.0)
    consecutive_trigger_days = _clip(np.rint(trigger_days * rng.uniform(0.25, 1.0, size=n_samples)), 0.0, 7.0)

    features = np.column_stack(
        [
            avg_temp,
            max_temp,
            total_rain,
            max_rain,
            trigger_days,
            avg_payout_pct,
            temp_variance,
            rain_variance,
            consecutive_trigger_days,
        ]
    ).astype(float)

    targets = np.clip(
        0.4 * (avg_temp / 50.0)
        + 0.3 * (total_rain / 300.0)
        + 0.2 * (trigger_days / 7.0)
        + 0.1 * (avg_payout_pct / 100.0),
        0.0,
        1.0,
    ).astype(float)

    return SyntheticRiskDataset(features=features, targets=targets, feature_names=FEATURE_NAMES.copy())
