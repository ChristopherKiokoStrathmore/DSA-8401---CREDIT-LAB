"""Train the fraud-flag pipeline on synthetic wallets and write the artifact.

Run from the repo root:

    python -m app.train
"""

from __future__ import annotations

import json
from importlib.metadata import version

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.features import (
    ARTIFACT_PATH,
    EXPECTED_SIGN,
    FEATURES,
    METADATA_PATH,
    MODEL_VERSION,
    RANDOM_STATE,
    TARGET,
)
from app.synthetic import generate

N_SAMPLES = 12000
TEST_SIZE = 0.20

def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=500,
                    solver="lbfgs",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def _positive_scores(pipeline: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    classes = list(pipeline.named_steps["clf"].classes_)
    positive = classes.index(1)
    return pipeline.predict_proba(frame)[:, positive]


def train(n_samples: int = N_SAMPLES, random_state: int = RANDOM_STATE) -> dict:
    df = generate(n=n_samples, random_state=random_state)
    X = df[FEATURES]
    y = df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=random_state,
        stratify=y,
    )

    pipeline = build_pipeline().fit(X_train, y_train)
    proba = _positive_scores(pipeline, X_test)

    dummy = DummyClassifier(strategy="prior").fit(X_train, y_train)
    dummy_proba = dummy.predict_proba(X_test)[:, list(dummy.classes_).index(1)]

    coefs = pipeline.named_steps["clf"].coef_[0]
    signs = {
        feature: int(np.sign(coef)) for feature, coef in zip(FEATURES, coefs)
    }
    flipped = [
        feature
        for feature, expected in EXPECTED_SIGN.items()
        if signs[feature] != expected
    ]
    if flipped:
        raise RuntimeError(
            "Coefficient signs flipped, so reason text would contradict "
            f"the model: {flipped}. Adjust the simulator and retrain."
        )

    metrics = {
        "test_roc_auc": float(roc_auc_score(y_test, proba)),
        "test_average_precision": float(average_precision_score(y_test, proba)),
        "test_brier": float(brier_score_loss(y_test, proba)),
        "dummy_prior_roc_auc": float(roc_auc_score(y_test, dummy_proba)),
        "dummy_prior_average_precision": float(
            average_precision_score(y_test, dummy_proba)
        ),
        "positive_rate_all": float(y.mean()),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }

    artifact = {
        "pipeline": pipeline,
        "features": FEATURES,
        "model_version": MODEL_VERSION,
        "random_state": random_state,
    }
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Local import keeps joblib next to the write, and matches the runtime loader.
    import joblib

    joblib.dump(artifact, ARTIFACT_PATH, compress=3)

    metadata = {
        "product": "Nairobi Fintech Fraud Flag API",
        "owner": "Christopher Nguu Kioko",
        "model_version": MODEL_VERSION,
        "algorithm": "StandardScaler + LogisticRegression",
        "label": (
            "Simulated fraud_flag on synthetic mobile-money wallets. "
            "Not estimated from real fraud cases."
        ),
        "data": {
            "source": "app.synthetic.generate",
            "n_samples": n_samples,
            "random_state": random_state,
            "pii": "none",
        },
        "features": FEATURES,
        "omitted_on_purpose": [
            "kyc_tier — a lower formal KYC tier must not raise the fraud flag",
            "gender, ethnicity, religion, precise location, name, MSISDN, national ID",
        ],
        "risk_bands": {
            "low": "probability < 0.30",
            "medium": "0.30 <= probability < 0.60",
            "high": "probability >= 0.60",
        },
        "metrics": metrics,
        "coefficient_signs": signs,
        "coefficients": {
            feature: float(coef) for feature, coef in zip(FEATURES, coefs)
        },
        "versions": {
            "scikit-learn": version("scikit-learn"),
            "numpy": version("numpy"),
            "pandas": version("pandas"),
            "joblib": version("joblib"),
        },
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main() -> None:
    metadata = train()
    metrics = metadata["metrics"]
    auc_lift = metrics["test_roc_auc"] - metrics["dummy_prior_roc_auc"]
    print(f"Wrote {ARTIFACT_PATH}")
    print(f"Wrote {METADATA_PATH}")
    print(
        f"Test ROC-AUC {metrics['test_roc_auc']:.3f} "
        f"(prior dummy {metrics['dummy_prior_roc_auc']:.3f}, "
        f"lift {auc_lift:.3f})"
    )
    print(
        f"Test average precision {metrics['test_average_precision']:.3f} "
        f"vs base rate {metrics['positive_rate_all']:.3f}"
    )
    print("Coefficient signs:", metadata["coefficient_signs"])


if __name__ == "__main__":
    main()
