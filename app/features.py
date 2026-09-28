"""Feature contract for the synthetic mobile-money fraud flag model.

No names, phone numbers, national IDs, or precise locations. Every column is a
behavioural or thin-file aggregate the caller already holds.
"""

from pathlib import Path

MODEL_VERSION = "0.1.0"
PRODUCT_NAME = "Nairobi Fintech Fraud Flag API"
RANDOM_STATE = 42

# Bands on the predicted fraud probability.
LOW_MAX = 0.30
MEDIUM_MAX = 0.60

DISCLAIMER = (
    "Synthetic demonstration score only. Not a finding of fraud, not a credit "
    "decision, and not an instruction to freeze an account. A person must "
    "review any adverse flag."
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / "models" / "nairobi_fraud_flag.joblib"
METADATA_PATH = REPO_ROOT / "models" / "metadata.json"

# Order is the model matrix order. Do not reorder without retraining.
FEATURES = [
    "account_age_days",
    "txn_count_30d",
    "avg_txn_amount_kes",
    "night_txn_ratio",
    "new_counterparty_ratio",
    "failed_txn_ratio",
    "device_change_count_90d",
    "sim_swap_90d",
    "airtime_topup_regularity",
    "utility_payment_count_90d",
    "merchant_payment_ratio",
    "savings_to_spend_ratio",
    "peer_transfer_velocity",
    "balance_volatility",
    "reactivation_burst",
]

TARGET = "fraud_flag"

# Expected sign of the logistic coefficient. +1 raises fraud log-odds.
# KYC tier is intentionally absent: a missing formal ID must not raise the flag.
EXPECTED_SIGN = {
    "account_age_days": -1,
    "txn_count_30d": 1,
    "avg_txn_amount_kes": 1,
    "night_txn_ratio": 1,
    "new_counterparty_ratio": 1,
    "failed_txn_ratio": 1,
    "device_change_count_90d": 1,
    "sim_swap_90d": 1,
    "airtime_topup_regularity": -1,
    "utility_payment_count_90d": -1,
    "merchant_payment_ratio": -1,
    "savings_to_spend_ratio": -1,
    "peer_transfer_velocity": 1,
    "balance_volatility": 1,
    "reactivation_burst": 1,
}

# Phrases keyed by the sign of (scaled value × coefficient).
# Positive contribution => the feature is pushing this wallet toward the flag.
REASON_UP = {
    "account_age_days": "Wallet history is short relative to typical scored wallets",
    "txn_count_30d": "Transaction count over 30 days is elevated",
    "avg_txn_amount_kes": "Average transaction size is high",
    "night_txn_ratio": "A large share of transactions happens overnight",
    "new_counterparty_ratio": "Many counterparties are new to this wallet",
    "failed_txn_ratio": "Failed transactions are unusually common",
    "device_change_count_90d": "The wallet changed devices repeatedly in 90 days",
    "sim_swap_90d": "A SIM swap was recorded in the last 90 days",
    "airtime_topup_regularity": "Airtime top-ups are irregular",
    "utility_payment_count_90d": "Utility-payment history on the wallet is thin",
    "merchant_payment_ratio": "Little of the flow is ordinary merchant spend",
    "savings_to_spend_ratio": "Little balance is held relative to spending",
    "peer_transfer_velocity": "Peer transfers are moving much faster than this wallet's usual pace",
    "balance_volatility": "Wallet balance is highly volatile",
    "reactivation_burst": "Activity resumed in a sharp burst after a quiet period",
}

REASON_DOWN = {
    "account_age_days": "The wallet has a longer operating history",
    "txn_count_30d": "Transaction count over 30 days is moderate",
    "avg_txn_amount_kes": "Average transaction size is moderate",
    "night_txn_ratio": "Most transactions happen in daytime hours",
    "new_counterparty_ratio": "Counterparties are mostly already known to the wallet",
    "failed_txn_ratio": "Failed transactions are rare",
    "device_change_count_90d": "The device profile has been stable",
    "sim_swap_90d": "No recent SIM swap is on the profile",
    "airtime_topup_regularity": "Regular airtime top-ups support a thin-file history",
    "utility_payment_count_90d": "Utility payments add an alternative-credit signal",
    "merchant_payment_ratio": "A solid share of payments goes to merchants",
    "savings_to_spend_ratio": "Savings relative to spend support a steadier wallet",
    "peer_transfer_velocity": "Peer-transfer pace is close to this wallet's usual level",
    "balance_volatility": "Balance has been relatively steady",
    "reactivation_burst": "No sharp reactivation burst is present",
}
