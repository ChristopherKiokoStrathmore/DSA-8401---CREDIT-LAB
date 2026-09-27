"""Load the committed artifact and turn one wallet into a score plus reasons."""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from app.features import (
    ARTIFACT_PATH,
    DISCLAIMER,
    FEATURES,
    LOW_MAX,
    MEDIUM_MAX,
    MODEL_VERSION,
    REASON_DOWN,
    REASON_UP,
)
from app.schemas import ScoreRequest, ScoreResponse, assert_feature_contract


def risk_band(probability: float) -> str:
    if probability < LOW_MAX:
        return "low"
    if probability < MEDIUM_MAX:
        return "medium"
    return "high"


def _load_artifact() -> dict:
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"Missing {ARTIFACT_PATH}. From the repo root run: python -m app.train"
        )
    artifact = joblib.load(ARTIFACT_PATH)
    if list(artifact["features"]) != FEATURES:
        raise RuntimeError(
            "Artifact feature list does not match app.features.FEATURES. Retrain."
        )
    if artifact["model_version"] != MODEL_VERSION:
        raise RuntimeError(
            "Artifact model_version does not match app.features.MODEL_VERSION."
        )
    return artifact


def _contributions(pipeline, frame: pd.DataFrame) -> np.ndarray:
    scaler = pipeline.named_steps["scaler"]
    clf = pipeline.named_steps["clf"]
    scaled = scaler.transform(frame[FEATURES])
    return scaled[0] * clf.coef_[0]


def explain(contributions: np.ndarray, band: str, k: int = 3) -> list[str]:
    """Short reasons aligned with the linear log-odds, not a second model."""
    phrases = REASON_UP if band in {"medium", "high"} else REASON_DOWN
    signed = contributions if band in {"medium", "high"} else -contributions
    order = np.argsort(-signed)
    reasons: list[str] = []
    for idx in order:
        feature = FEATURES[int(idx)]
        # Skip reasons that point the other way once we already have one.
        if signed[idx] <= 0 and reasons:
            break
        reasons.append(phrases[feature])
        if len(reasons) == k:
            break
    if not reasons:
        reasons.append("No single feature dominates this score")
    return reasons


class Scorer:
    def __init__(self) -> None:
        assert_feature_contract()
        artifact = _load_artifact()
        self.pipeline = artifact["pipeline"]
        self.model_version = artifact["model_version"]
        self.metadata = {}
        meta_path = ARTIFACT_PATH.with_name("metadata.json")
        if meta_path.exists():
            self.metadata = json.loads(meta_path.read_text())

    def score(self, payload: ScoreRequest) -> ScoreResponse:
        frame = pd.DataFrame([payload.model_dump()])[FEATURES].astype(float)
        classes = list(self.pipeline.named_steps["clf"].classes_)
        positive = classes.index(1)
        probability = float(self.pipeline.predict_proba(frame)[0, positive])
        probability = float(np.clip(round(probability, 6), 0.0, 1.0))
        band = risk_band(probability)
        return ScoreResponse(
            probability=probability,
            risk_band=band,
            reasons=explain(_contributions(self.pipeline, frame), band),
            model_version=self.model_version,
            disclaimer=DISCLAIMER,
        )


_SCORER: Scorer | None = None


def get_scorer() -> Scorer:
    global _SCORER
    if _SCORER is None:
        _SCORER = Scorer()
    return _SCORER
