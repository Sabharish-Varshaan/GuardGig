from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier

from .data_generator import generate_synthetic_risk_dataset


def train_risk_model(output_dir: Path | None = None, n_samples: int = 3000, random_state: int = 42) -> Path:
    output_dir = output_dir or Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = generate_synthetic_risk_dataset(n_samples=n_samples, random_state=random_state)
    base_model = GradientBoostingClassifier(random_state=random_state)
    try:
        model = CalibratedClassifierCV(estimator=base_model, method="sigmoid", cv=3)
    except TypeError:
        # Backward compatibility for older sklearn versions.
        model = CalibratedClassifierCV(base_estimator=base_model, method="sigmoid", cv=3)

    model.fit(dataset.features, dataset.targets)

    model_path = output_dir / "risk_model.pkl"
    joblib.dump(model, model_path)
    return model_path


if __name__ == "__main__":
    saved_path = train_risk_model()
    print(f"Saved risk model to {saved_path}")