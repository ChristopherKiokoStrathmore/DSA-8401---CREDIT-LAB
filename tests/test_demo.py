"""Smoke test for the browser demo. Presets are the example JSON wallets."""

import json
import re

from fastapi.testclient import TestClient

from app.features import FEATURES
from app.main import app
from app.profiles import ESTABLISHED_WALLET, SUSPECTED_MULE, THIN_FILE_INCLUSION

client = TestClient(app)

PRESET_WALLETS = {
    "established": ESTABLISHED_WALLET,
    "thin_file": THIN_FILE_INCLUSION,
    "mule": SUSPECTED_MULE,
}


def _demo_html(path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    return response.text


def _embedded_config(html: str) -> dict:
    match = re.search(
        r'<script id="demo-config" type="application/json">(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    assert match, "demo page is missing the preset config"
    return json.loads(match.group(1))


def test_demo_page_returns_html():
    page = _demo_html("/")
    assert _demo_html("/demo") == page
    lowered = page.lower()
    assert "nairobi fintech fraud flag" in lowered
    assert "not production credit scoring" in lowered
    assert "training data is synthetic" in lowered
    assert "roc-auc ~0.79 is simulator recovery only" in lowered
    assert "owner: christopher nguu" in lowered
    assert "nguu kioko" not in lowered
    assert "established wallet" in lowered
    assert "young thin-file" in lowered
    assert "suspected mule" in lowered
    names = set(re.findall(r'name="([^"]+)"', page))
    assert set(FEATURES).issubset(names)
    assert names.isdisjoint({"kyc_tier", "msisdn", "phone", "phone_number", "national_id"})
    assert "__PRODUCT__" not in page
    assert "__DEMO_CONFIG__" not in page


def test_demo_presets_match_examples_and_score():
    config = _embedded_config(_demo_html("/"))
    assert [item["id"] for item in config["presets"]] == list(PRESET_WALLETS)
    bands = {}
    for item in config["presets"]:
        assert item["values"] == PRESET_WALLETS[item["id"]]
        response = client.post("/score", json=item["values"])
        assert response.status_code == 200
        body = response.json()
        assert 0.0 <= body["probability"] <= 1.0
        assert 1 <= len(body["reasons"]) <= 3
        bands[item["id"]] = body["risk_band"]
    assert bands["established"] == "low"
    assert bands["thin_file"] != "high"
    assert bands["mule"] == "high"
