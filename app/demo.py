"""Browser demo for reviewers who should not have to use curl.

Presets are the JSON files in ``examples/``. Field limits come from the
``/score`` schema, so the form cannot drift from the API contract.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from app.features import (
    DISCLAIMER,
    FEATURES,
    LOW_MAX,
    MEDIUM_MAX,
    METADATA_PATH,
    MODEL_VERSION,
    PRODUCT_NAME,
    REPO_ROOT,
)
from app.schemas import ScoreRequest

_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "demo.html"

# Labels are presentation only. The posted names stay the feature contract.
LABELS = {
    "account_age_days": "Account age (days)",
    "txn_count_30d": "Transactions, 30 days",
    "avg_txn_amount_kes": "Average amount (KES)",
    "night_txn_ratio": "Overnight share",
    "new_counterparty_ratio": "New counterparties",
    "failed_txn_ratio": "Failed-transaction share",
    "device_change_count_90d": "Device changes, 90 days",
    "sim_swap_90d": "SIM swap, 90 days",
    "airtime_topup_regularity": "Airtime top-up regularity",
    "utility_payment_count_90d": "Utility payments, 90 days",
    "merchant_payment_ratio": "Merchant payment share",
    "savings_to_spend_ratio": "Savings to spend",
    "peer_transfer_velocity": "Peer-transfer velocity",
    "balance_volatility": "Balance volatility",
    "reactivation_burst": "Reactivation burst",
}

GROUPS = (
    (
        "Activity",
        (
            "account_age_days",
            "txn_count_30d",
            "avg_txn_amount_kes",
            "night_txn_ratio",
            "new_counterparty_ratio",
            "failed_txn_ratio",
            "peer_transfer_velocity",
            "balance_volatility",
            "reactivation_burst",
        ),
    ),
    (
        "Device",
        (
            "device_change_count_90d",
            "sim_swap_90d",
        ),
    ),
    (
        "Thin-file signals",
        (
            "airtime_topup_regularity",
            "utility_payment_count_90d",
            "merchant_payment_ratio",
            "savings_to_spend_ratio",
        ),
    ),
)

# Order matches the review story: ordinary wallet, inclusion case, adverse pattern.
PRESET_SPECS = (
    (
        "established",
        "established_wallet.json",
        "Established wallet",
        "Longer history, daytime activity, and ordinary merchant spend.",
    ),
    (
        "thin_file",
        "thin_file_inclusion.json",
        "Young thin-file",
        "A new wallet with regular airtime, utility bills, and merchant payments.",
    ),
    (
        "mule",
        "suspected_mule.json",
        "Suspected mule",
        "Overnight transfers, new counterparties, device churn, and a SIM swap.",
    ),
)


def _check_contract() -> None:
    grouped = [name for _, names in GROUPS for name in names]
    if len(grouped) != len(set(grouped)) or set(grouped) != set(FEATURES):
        raise RuntimeError("Demo field groups do not match FEATURES")
    if set(LABELS) != set(FEATURES):
        raise RuntimeError("Demo labels do not match FEATURES")


def _metadata() -> dict:
    if not METADATA_PATH.exists():
        return {}
    return json.loads(METADATA_PATH.read_text())


def _field_specs() -> dict[str, dict]:
    properties = ScoreRequest.model_json_schema()["properties"]
    specs: dict[str, dict] = {}
    for name in FEATURES:
        prop = properties[name]
        binary = prop.get("enum") == [0, 1]
        if binary:
            kind = "binary"
        elif prop.get("type") == "integer":
            kind = "integer"
        else:
            kind = "number"
        specs[name] = {
            "label": LABELS[name],
            "description": prop["description"],
            "minimum": prop.get("minimum"),
            "maximum": prop.get("maximum"),
            "kind": kind,
        }
    return specs


def _load_presets() -> list[dict]:
    presets = []
    for preset_id, filename, label, summary in PRESET_SPECS:
        path = REPO_ROOT / "examples" / filename
        values = json.loads(path.read_text())
        if list(values) != FEATURES:
            raise RuntimeError(f"{filename} keys do not match FEATURES")
        presets.append(
            {
                "id": preset_id,
                "file": filename,
                "label": label,
                "summary": summary,
                "values": values,
            }
        )
    return presets


def _format_value(value: object) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        text = format(value, "f").rstrip("0").rstrip(".")
        return text or "0"
    return str(value)


def _preset_html(presets: list[dict]) -> str:
    parts = []
    for preset in presets:
        pressed = "true" if preset["id"] == "established" else "false"
        parts.append(
            '<button type="button" class="preset" '
            f'data-preset="{escape(preset["id"])}" aria-pressed="{pressed}">'
            f'<span class="preset-title">{escape(preset["label"])}</span>'
            f'<span class="preset-copy">{escape(preset["summary"])}</span>'
            "</button>"
        )
    return "\n".join(parts)


def _fields_html(specs: dict[str, dict], defaults: dict) -> str:
    blocks = []
    for title, names in GROUPS:
        fields = []
        for name in names:
            spec = specs[name]
            kind = spec["kind"]
            value = defaults[name]
            if kind == "binary":
                options = []
                for option, caption in ((0, "0 - No"), (1, "1 - Yes")):
                    selected = " selected" if int(value) == option else ""
                    options.append(
                        f'<option value="{option}"{selected}>{caption}</option>'
                    )
                control = (
                    f'<select id="f-{name}" name="{name}" data-kind="binary">'
                    + "".join(options)
                    + "</select>"
                )
            else:
                step = "1" if kind == "integer" else "any"
                mode = "numeric" if kind == "integer" else "decimal"
                control = (
                    f'<input id="f-{name}" name="{name}" data-kind="{kind}" '
                    f'type="number" min="{spec["minimum"]}" max="{spec["maximum"]}" '
                    f'step="{step}" inputmode="{mode}" required '
                    f'value="{escape(_format_value(value))}">'
                )
            fields.append(
                '<label class="field">'
                f'<span class="field-name">{escape(spec["label"])}</span>'
                f"{control}"
                f'<span class="hint">{escape(spec["description"])}</span>'
                "</label>"
            )
        blocks.append(
            "<fieldset>"
            f"<legend>{escape(title)}</legend>"
            f'<div class="fields">{"".join(fields)}</div>'
            "</fieldset>"
        )
    return "".join(blocks)


def _caveat(metadata: dict) -> str:
    metrics = metadata.get("metrics") or {}
    auc = metrics.get("test_roc_auc", 0.79)
    shown = f"{float(auc):.2f}"
    return (
        f"Training data is synthetic. ROC-AUC ~{shown} is simulator recovery only, "
        "not a field false-positive rate."
    )


def _band_key() -> str:
    return (
        f"Low below {LOW_MAX:.2f} · medium below {MEDIUM_MAX:.2f} · "
        f"high from {MEDIUM_MAX:.2f}."
    )


def render_demo_page() -> str:
    """Return the single-page demo. Safe to call on every request."""
    _check_contract()
    metadata = _metadata()
    presets = _load_presets()
    specs = _field_specs()
    defaults = presets[0]["values"]
    config = {
        "presets": [
            {"id": preset["id"], "values": preset["values"]} for preset in presets
        ]
    }
    payload = json.dumps(config, separators=(",", ":")).replace("<", "\\u003c")
    owner = str(metadata.get("owner") or "Christopher Nguu Kioko")
    html = _TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "__PRODUCT__": escape(PRODUCT_NAME),
        "__MODEL_VERSION__": escape(MODEL_VERSION),
        "__OWNER__": escape(owner),
        "__CAVEAT__": escape(_caveat(metadata)),
        "__BAND_KEY__": escape(_band_key()),
        "__DISCLAIMER__": escape(DISCLAIMER),
        "__PRESETS__": _preset_html(presets),
        "__FIELDS__": _fields_html(specs, defaults),
        "__DEMO_CONFIG__": payload,
    }
    for token, value in replacements.items():
        html = html.replace(token, value)
    return html
