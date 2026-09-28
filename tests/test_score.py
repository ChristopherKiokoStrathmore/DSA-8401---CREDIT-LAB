"""API checks for POST /score. Wallets are the fixed synthetic profiles."""

import json

from fastapi.testclient import TestClient

from app.features import FEATURES, REPO_ROOT
from app.main import app
from app.profiles import (
    ESTABLISHED_WALLET,
    SUSPECTED_MULE,
    THIN_FILE_INCLUSION,
)
from app.schemas import ScoreRequest

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["product"] == "Nairobi Fintech Fraud Flag API"
    assert body["model_version"]
    assert "synthetic" in body["data_policy"]


def test_score_contract_and_low_band():
    response = client.post("/score", json=ESTABLISHED_WALLET)
    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["probability"] <= 1.0
    assert body["risk_band"] == "low"
    assert 1 <= len(body["reasons"]) <= 3
    assert all(isinstance(reason, str) and reason.strip() for reason in body["reasons"])
    assert "synthetic" in body["disclaimer"].lower()


def test_thin_file_is_not_high_and_mule_is_higher():
    inclusion = client.post("/score", json=THIN_FILE_INCLUSION)
    mule = client.post("/score", json=SUSPECTED_MULE)
    assert inclusion.status_code == 200
    assert mule.status_code == 200
    inclusion_body = inclusion.json()
    mule_body = mule.json()
    assert inclusion_body["risk_band"] in {"low", "medium"}
    assert inclusion_body["risk_band"] != "high"
    assert mule_body["risk_band"] == "high"
    assert mule_body["probability"] > inclusion_body["probability"]
    assert 1 <= len(mule_body["reasons"]) <= 3


def test_score_rejects_missing_field_and_out_of_range():
    missing = dict(ESTABLISHED_WALLET)
    del missing["sim_swap_90d"]
    assert client.post("/score", json=missing).status_code == 422

    out_of_range = dict(ESTABLISHED_WALLET)
    out_of_range["night_txn_ratio"] = 1.4
    assert client.post("/score", json=out_of_range).status_code == 422

    extra = dict(ESTABLISHED_WALLET)
    extra["msisdn"] = "+254700000000"
    assert client.post("/score", json=extra).status_code == 422


def test_schema_and_example_files_match_the_feature_contract():
    assert list(ScoreRequest.model_fields) == FEATURES
    expected = {
        "established_wallet.json": ESTABLISHED_WALLET,
        "thin_file_inclusion.json": THIN_FILE_INCLUSION,
        "suspected_mule.json": SUSPECTED_MULE,
    }
    for name, payload in expected.items():
        on_disk = json.loads((REPO_ROOT / "examples" / name).read_text())
        assert on_disk == payload
        assert list(on_disk) == FEATURES
