"""Request and response models for POST /score and GET /health."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.features import DISCLAIMER, FEATURES, PRODUCT_NAME
from app.profiles import ESTABLISHED_WALLET


class ScoreRequest(BaseModel):
    """One synthetic wallet. Field order matches the trained model matrix."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [ESTABLISHED_WALLET]},
    )

    account_age_days: int = Field(
        ge=1,
        le=5000,
        description="Days since the mobile-money wallet was opened.",
    )
    txn_count_30d: int = Field(
        ge=0,
        le=500,
        description="Completed transactions in the last 30 days.",
    )
    avg_txn_amount_kes: float = Field(
        ge=0,
        le=1_000_000,
        description="Average completed transaction size in Kenyan shillings.",
    )
    night_txn_ratio: float = Field(
        ge=0,
        le=1,
        description="Share of recent transactions between 00:00 and 05:00 local time.",
    )
    new_counterparty_ratio: float = Field(
        ge=0,
        le=1,
        description="Share of 30-day counterparties never seen on this wallet before.",
    )
    failed_txn_ratio: float = Field(
        ge=0,
        le=1,
        description="Failed attempts divided by failed plus completed attempts, last 30 days.",
    )
    device_change_count_90d: int = Field(
        ge=0,
        le=30,
        description="Distinct device changes observed in 90 days.",
    )
    sim_swap_90d: Literal[0, 1] = Field(
        description="1 if a SIM swap was recorded in the last 90 days, else 0.",
    )
    airtime_topup_regularity: float = Field(
        ge=0,
        le=1,
        description="0–1 regularity of airtime top-ups. Higher means a steadier cadence.",
    )
    utility_payment_count_90d: int = Field(
        ge=0,
        le=90,
        description="Electricity, water, or similar bill payments in 90 days.",
    )
    merchant_payment_ratio: float = Field(
        ge=0,
        le=1,
        description="Share of 30-day outflow that went to merchants rather than persons.",
    )
    savings_to_spend_ratio: float = Field(
        ge=0,
        le=50,
        description="Typical wallet savings divided by typical monthly outflow.",
    )
    peer_transfer_velocity: float = Field(
        ge=0,
        le=100,
        description="Recent peer-transfer pace divided by this wallet's own prior pace. 1 is normal.",
    )
    balance_volatility: float = Field(
        ge=0,
        le=1,
        description="0–1 scaled volatility of end-of-day balance over 30 days.",
    )
    reactivation_burst: Literal[0, 1] = Field(
        description="1 if a quiet wallet suddenly resumed with a burst of transfers.",
    )


class ScoreResponse(BaseModel):
    probability: float = Field(ge=0, le=1)
    risk_band: Literal["low", "medium", "high"]
    reasons: list[str] = Field(min_length=1, max_length=3)
    model_version: str
    disclaimer: str = DISCLAIMER


class HealthResponse(BaseModel):
    status: Literal["ok"]
    product: str = PRODUCT_NAME
    model_version: str
    data_policy: str


def assert_feature_contract() -> None:
    """Fail fast if the API schema drifts from the model matrix."""
    if list(ScoreRequest.model_fields) != FEATURES:
        raise RuntimeError("ScoreRequest fields do not match FEATURES")
