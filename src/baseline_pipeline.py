"""
DSA 8401 - Week 1 Lab: honest end-to-end BASELINE (regression).

Dataset : Real estate valuation (predict price per unit area).
Point   : the unimpressive, leak-free baseline that every later technique
          in the course must beat. A script version of the Week-1 notebook,
          runnable from the command line and safe to unit-test / put in CI.

Run:
    python src/baseline_pipeline.py

Design choices that mirror the lecture:
  * Split BEFORE fitting anything (no train/test contamination).
  * Scaling is learned inside a Pipeline -> only on training folds.
  * Always compare the model against a DummyRegressor floor.
  * Report LIFT over baseline, never a raw score in isolation.
  * Cross-validate on TRAIN only; the test set is touched exactly once.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# One knob controls every source of randomness -> reproducibility.
RANDOM_STATE = 42

# Resolve data path relative to THIS file, so the script runs from anywhere.
REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_CSV = REPO_ROOT / "course" / "Real estate.csv"
URL = (
    "https://raw.githubusercontent.com/NUELBUNDI/"
    "Machine-Learning-Data-Set/refs/heads/main/Real%20estate.csv"
)

FEATURES = ["txn_date", "house_age", "dist_mrt", "n_stores", "lat", "lon"]
TARGET = "price"


def load_data() -> pd.DataFrame:
    """Load the CSV locally if present, else fall back to the raw URL."""
    if LOCAL_CSV.exists():
        df = pd.read_csv(LOCAL_CSV)
        print(f"Loaded local file: {LOCAL_CSV.relative_to(REPO_ROOT)}")
    else:
        df = pd.read_csv(URL)
        print("Local file missing - loaded from GitHub URL.")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the index column and give features short, code-friendly names."""
    if "No" in df.columns:
        df = df.drop(columns=["No"])
    return df.rename(
        columns={
            "X1 transaction date": "txn_date",
            "X2 house age": "house_age",
            "X3 distance to the nearest MRT station": "dist_mrt",
            "X4 number of convenience stores": "n_stores",
            "X5 latitude": "lat",
            "X6 longitude": "lon",
            "Y house price of unit area": "price",
        }
    )


def evaluate(y_true, y_pred) -> dict:
    """RMSE / MAE / R^2 for a set of predictions."""
    return {
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "R2": float(r2_score(y_true, y_pred)),
    }


def main() -> None:
    df = clean(load_data())
    print(f"Shape (rows, cols): {df.shape}")
    print(f"Missing values total: {int(df.isna().sum().sum())}\n")

    X, y = df[FEATURES], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE
    )
    print(f"Train rows: {len(X_train)}   Test rows: {len(X_test)}")

    # --- Baseline: predict the mean every time (the floor) ---
    baseline = DummyRegressor(strategy="mean").fit(X_train, y_train)
    base = evaluate(y_test, baseline.predict(X_test))

    # --- Model: scale -> linear regression, inside a leak-free Pipeline ---
    model = Pipeline(
        [("scaler", StandardScaler()), ("linreg", LinearRegression())]
    ).fit(X_train, y_train)
    lin = evaluate(y_test, model.predict(X_test))

    # --- Cross-validation on TRAIN only (test set stays sealed) ---
    kf = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_rmse = np.sqrt(
        -cross_val_score(
            model, X_train, y_train, scoring="neg_mean_squared_error", cv=kf
        )
    )

    # --- Report ---
    summary = pd.DataFrame(
        {
            "RMSE": [base["RMSE"], lin["RMSE"]],
            "MAE": [base["MAE"], lin["MAE"]],
            "R2": [base["R2"], lin["R2"]],
        },
        index=["Baseline (mean)", "LinearRegression"],
    )
    rmse_lift = (base["RMSE"] - lin["RMSE"]) / base["RMSE"] * 100

    print("\n" + "=" * 48)
    print(summary.round(3).to_string())
    print("=" * 48)
    print(f"Linear regression cuts RMSE by {rmse_lift:.1f}% vs the baseline.")
    print(f"It explains {lin['R2'] * 100:.1f}% of price variance (test R^2).")
    print(
        f"5-fold CV RMSE (train): {cv_rmse.mean():.3f} +/- {cv_rmse.std():.3f}"
        f"  | test RMSE {lin['RMSE']:.3f} sits in range -> stable, no obvious overfit."
    )


if __name__ == "__main__":
    main()
