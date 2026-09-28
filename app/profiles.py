"""Fixed synthetic wallets used by the README, /docs examples, and tests.

These are invented aggregates. They are not drawn from a customer database.
"""

ESTABLISHED_WALLET = {
    "account_age_days": 940,
    "txn_count_30d": 14,
    "avg_txn_amount_kes": 850.0,
    "night_txn_ratio": 0.04,
    "new_counterparty_ratio": 0.08,
    "failed_txn_ratio": 0.01,
    "device_change_count_90d": 0,
    "sim_swap_90d": 0,
    "airtime_topup_regularity": 0.86,
    "utility_payment_count_90d": 4,
    "merchant_payment_ratio": 0.48,
    "savings_to_spend_ratio": 0.70,
    "peer_transfer_velocity": 0.90,
    "balance_volatility": 0.12,
    "reactivation_burst": 0,
}

# New wallet, no bureau file, but regular airtime, utilities, and merchant spend.
# Youth and thin formal history must not, on their own, produce a high flag.
THIN_FILE_INCLUSION = {
    "account_age_days": 55,
    "txn_count_30d": 11,
    "avg_txn_amount_kes": 620.0,
    "night_txn_ratio": 0.06,
    "new_counterparty_ratio": 0.12,
    "failed_txn_ratio": 0.02,
    "device_change_count_90d": 0,
    "sim_swap_90d": 0,
    "airtime_topup_regularity": 0.90,
    "utility_payment_count_90d": 5,
    "merchant_payment_ratio": 0.62,
    "savings_to_spend_ratio": 0.55,
    "peer_transfer_velocity": 1.0,
    "balance_volatility": 0.15,
    "reactivation_burst": 0,
}

SUSPECTED_MULE = {
    "account_age_days": 18,
    "txn_count_30d": 72,
    "avg_txn_amount_kes": 7400.0,
    "night_txn_ratio": 0.71,
    "new_counterparty_ratio": 0.83,
    "failed_txn_ratio": 0.28,
    "device_change_count_90d": 4,
    "sim_swap_90d": 1,
    "airtime_topup_regularity": 0.08,
    "utility_payment_count_90d": 0,
    "merchant_payment_ratio": 0.05,
    "savings_to_spend_ratio": 0.02,
    "peer_transfer_velocity": 4.8,
    "balance_volatility": 0.78,
    "reactivation_burst": 1,
}
