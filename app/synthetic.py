"""Synthetic mobile-money wallets and a simulated fraud label.

Features are drawn with their own noise, then 18% of rows are overwritten as
thin-file inclusion wallets (young, calm behaviour, steady alternative-credit
signals). The label is a noisy function of those features. Hold-out scores
measure recovery of this simulation, not live Nairobi fraud prevalence.

Nothing here is a real customer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.features import FEATURES, RANDOM_STATE, TARGET

INCLUSION_SHARE = 0.18


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0)))


def _beta(rng: np.random.Generator, a: float, b: float, n: int) -> np.ndarray:
    return np.clip(rng.beta(a, b, size=n), 0.0, 1.0)


def _apply_inclusion(rng: np.random.Generator, columns: dict[str, np.ndarray]) -> None:
    """Young wallets with ordinary bill-pay and airtime, and little fraud behaviour.

    Without this slice, account age becomes a stand-in for the fraud label and
    a new customer is flagged for being new.
    """
    n = len(columns["account_age_days"])
    mask = rng.random(n) < INCLUSION_SHARE
    k = int(mask.sum())
    columns["account_age_days"][mask] = rng.integers(14, 150, k)
    columns["txn_count_30d"][mask] = np.clip(rng.normal(12, 4, k), 1, 40)
    columns["avg_txn_amount_kes"][mask] = np.clip(rng.lognormal(6.3, 0.35, k), 50, 4000)
    columns["night_txn_ratio"][mask] = _beta(rng, 1.5, 18, k)
    columns["new_counterparty_ratio"][mask] = _beta(rng, 2.0, 12, k)
    columns["failed_txn_ratio"][mask] = _beta(rng, 1.2, 40, k)
    columns["device_change_count_90d"][mask] = rng.binomial(1, 0.15, k)
    columns["sim_swap_90d"][mask] = rng.binomial(1, 0.01, k)
    columns["airtime_topup_regularity"][mask] = _beta(rng, 10, 1.8, k)
    columns["utility_payment_count_90d"][mask] = np.clip(rng.poisson(4, k), 1, 10)
    columns["merchant_payment_ratio"][mask] = _beta(rng, 7.0, 2.5, k)
    columns["savings_to_spend_ratio"][mask] = np.clip(
        rng.lognormal(-0.4, 0.3, k), 0.05, 3
    )
    columns["peer_transfer_velocity"][mask] = np.clip(
        rng.lognormal(0.0, 0.2, k), 0.2, 2.5
    )
    columns["balance_volatility"][mask] = _beta(rng, 2.0, 10, k)
    columns["reactivation_burst"][mask] = 0.0


def generate(n: int = 12000, random_state: int = RANDOM_STATE) -> pd.DataFrame:
    """Build n synthetic wallets and a simulated fraud_flag."""
    if n < 100:
        raise ValueError("n must be at least 100")

    rng = np.random.default_rng(random_state)
    columns = {
        "account_age_days": rng.integers(10, 2000, n).astype(float),
        "txn_count_30d": np.clip(rng.normal(22, 18, n), 0, 180),
        "avg_txn_amount_kes": np.clip(rng.lognormal(6.7, 0.85, n), 20, 80_000),
        "night_txn_ratio": _beta(rng, 2.0, 6.0, n),
        "new_counterparty_ratio": _beta(rng, 2.2, 5.5, n),
        "failed_txn_ratio": _beta(rng, 1.4, 12, n),
        "device_change_count_90d": np.clip(rng.poisson(0.6, n), 0, 10).astype(float),
        "sim_swap_90d": rng.binomial(1, 0.08, n).astype(float),
        "airtime_topup_regularity": _beta(rng, 4.5, 2.4, n),
        "utility_payment_count_90d": np.clip(rng.poisson(2.2, n), 0, 12).astype(float),
        "merchant_payment_ratio": _beta(rng, 3.5, 3.5, n),
        "savings_to_spend_ratio": np.clip(rng.lognormal(-0.7, 0.7, n), 0, 6),
        "peer_transfer_velocity": np.clip(rng.lognormal(0.15, 0.55, n), 0, 10),
        "balance_volatility": _beta(rng, 2.4, 4.5, n),
        "reactivation_burst": rng.binomial(1, 0.08, n).astype(float),
    }
    _apply_inclusion(rng, columns)

    logit = (
        -3.3
        + 2.6 * columns["night_txn_ratio"]
        + 2.4 * columns["new_counterparty_ratio"]
        + 3.2 * columns["failed_txn_ratio"]
        + 0.55 * columns["device_change_count_90d"]
        + 2.0 * columns["sim_swap_90d"]
        + 0.60 * columns["peer_transfer_velocity"]
        + 1.6 * columns["balance_volatility"]
        + 1.35 * columns["reactivation_burst"]
        + 0.85 * (np.log1p(columns["avg_txn_amount_kes"]) / np.log1p(2000.0))
        + 0.015 * columns["txn_count_30d"]
        - 0.00035 * columns["account_age_days"]
        - 1.6 * columns["airtime_topup_regularity"]
        - 0.24 * columns["utility_payment_count_90d"]
        - 1.0 * columns["merchant_payment_ratio"]
        - 0.60 * np.minimum(columns["savings_to_spend_ratio"], 2.5)
        + rng.normal(0.0, 0.70, n)
    )
    frame = pd.DataFrame(columns)
    frame[TARGET] = rng.binomial(1, _sigmoid(logit)).astype(int)
    return frame[FEATURES + [TARGET]]
