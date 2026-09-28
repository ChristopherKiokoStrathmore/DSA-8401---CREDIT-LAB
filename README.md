# Nairobi Fintech Fraud Flag API

Owner: **Christopher Nguu Kioko**

A small, demoable scoring service for the UNECA African AI Innovators showcase
(deadline ~2 October 2026). `POST /score` turns synthetic mobile-money and
thin-file aggregates into a fraud **probability**, a **risk band**, and up to
three short **reasons**.

The Week 1 credit-lab baseline is still in this repository. It is a leak-free
regression on a public real-estate table. This API is a separate classification
product built for the showcase. See [Why this name](#why-this-name) and
[Week 1 lab](#week-1-lab-preserved).

## Why this name

The course repository is a credit lab, and the Week 1 lecture tells a
credit-scoring story. The code that was already here predicts **price per unit
area**, not default. A pure alternative-credit probability-of-default model
would not match that baseline, and it would overclaim what a two-week demo can
know about repayment.

The showcase product is therefore the **Nairobi Fintech Fraud Flag API**: a
fraud-flag classifier on synthetic wallet behaviour. Alternative-credit signals
are inputs, not a second score. Regular airtime top-ups, utility payments,
merchant spend, and savings-to-spend can pull the fraud probability **down**,
so a new wallet without a bureau file is not treated as suspicious just because
it is new. Formal KYC tier is omitted on purpose. A lower KYC tier must not
raise the flag.

## Problem

Mobile money is how a large share of East African households save, get paid, and
pay bills. The same rails are abused by SIM-swap takeovers, mule wallets, and
overnight pass-through bursts. Those losses fall on customers who can least
afford them, and blunt fraud rules then punish the thin-file majority: young
wallets, informal traders, and anyone a traditional bureau has never seen.

This demo asks a narrower question than “should this person get a loan?”:

> Given **synthetic** behavioural aggregates for one wallet, what is the
> probability that the pattern resembles the simulated fraud process, which
> band does that sit in, and which features drove the score?

It does not accuse a person, decline credit, or file a suspicious-transaction
report. A human reviewer has to sit in front of any adverse flag.

## How to run

Python 3.11 or newer. From the repository root:

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The committed model artifact loads at startup. Interactive docs (useful on a
showcase laptop) are at <http://127.0.0.1:8000/docs>.

Check the process, then score the two checked-in wallets:

```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/score \
  -H 'Content-Type: application/json' \
  -d @examples/established_wallet.json

curl -s -X POST http://127.0.0.1:8000/score \
  -H 'Content-Type: application/json' \
  -d @examples/suspected_mule.json
```

A thin-file inclusion example (new wallet, steady airtime and utility payments)
is in `examples/thin_file_inclusion.json`. Tests:

```bash
pytest
```

Retrain only if you change `app/synthetic.py` or the feature list. The script
rewrites `models/nairobi_fraud_flag.joblib` and `models/metadata.json`:

```bash
python -m app.train
```

## What `/score` returns

`GET /health` → `status`, product name, model version, data policy.

`POST /score` accepts one JSON object. Unknown fields are rejected, including
anything that looks like a phone number or national ID. Response:

| Field | Meaning |
| --- | --- |
| `probability` | Predicted probability of the **simulated** fraud label, from 0 to 1 |
| `risk_band` | `low` below 0.30, `medium` from 0.30 up to but not including 0.60, `high` at 0.60 and above |
| `reasons` | Up to three short phrases from the largest log-odds contributions |
| `model_version` | Artifact version (`0.1.0`) |
| `disclaimer` | Reminder that this is not an operational decision |

Reasons for `medium` and `high` name the features pushing the score up. Reasons
for `low` name the features pulling it down, including alternative-credit
signals when those dominate.

### Features

All of these are aggregates. Do not send names, MSISDNs, device identifiers, or
coordinates.

| Feature | Role in the demo |
| --- | --- |
| `account_age_days` | Longer history pulls risk down slightly. Age alone is a weak term. |
| `txn_count_30d`, `avg_txn_amount_kes` | Recent activity level and typical ticket size (KES). |
| `night_txn_ratio` | Share of transactions between 00:00 and 05:00. |
| `new_counterparty_ratio` | Share of counterparties new to this wallet. |
| `failed_txn_ratio` | Failed attempts over failed plus completed. |
| `device_change_count_90d`, `sim_swap_90d` | Device churn and a recent SIM swap. |
| `peer_transfer_velocity`, `balance_volatility`, `reactivation_burst` | Pace versus this wallet’s own norm, balance swings, quiet-then-burst. |
| `airtime_topup_regularity`, `utility_payment_count_90d`, `merchant_payment_ratio`, `savings_to_spend_ratio` | Thin-file / alternative-credit signals that can lower the flag. |

## Model

`models/nairobi_fraud_flag.joblib` is a scikit-learn `Pipeline`: `StandardScaler`
then `LogisticRegression`, fit on 12,000 synthetic wallets from
`app.synthetic.generate` (`random_state=42`). The split is 80/20, stratified,
and the test fold is scored once. A `DummyClassifier(strategy="prior")` is the
floor reported in `models/metadata.json`. Hold-out ROC-AUC on this simulation is
about 0.79. The label is a noisy function of the same features, so that figure
measures recovery of the simulator. It is **not** a field false-positive rate
and must not be quoted as one.

The Week 1 discipline still applies: scale inside the pipeline, compare with a
dummy, do not treat a raw score as if it were a decision.

## Ethics

- **Synthetic data only.** The generator invents wallets. The API does not
  accept or store PII. The original lab CSV is a public property-price table,
  not a customer extract, and the fraud model does not read it.
- **Not an accusation.** A high band means “this synthetic pattern matches the
  simulator,” not “this person committed fraud.”
- **Human review.** Do not auto-freeze a wallet, file a law-enforcement report,
  or decline a loan from this response.
- **Inclusion.** Young wallets with regular airtime, utility payments, merchant
  spend, and savings are in the training mix specifically so thin files are not
  collapsed into the fraud class. KYC tier is not a feature.
- **No protected attributes.** Gender, ethnicity, religion, and precise location
  are not inputs. Reason codes are feature phrases, not demographic labels.
- **Honest metrics.** Publishing the simulated AUC as real-world performance
  would mislead a regulator, a lender, or a showcase jury.

## SDG and Agenda 2063

Safer mobile money and a route into finance for people without a bureau file
sit on two African policy tracks this demo is built to illustrate.

**Sustainable Development Goals**

- **SDG 1** (no poverty) and **SDG 8** (decent work and economic growth): fraud
  losses and locked accounts both push people out of the digital economy.
- **SDG 9** (industry, innovation, and infrastructure): the score runs on
  ordinary wallet aggregates, the kind a licensed fintech already stores.
- **SDG 10** (reduced inequalities): alternative-credit signals are allowed to
  lower the flag for thin-file customers instead of copying a bureau that has
  never seen them.
- **SDG 16** (peace, justice, and strong institutions): a flag without a human
  reviewer and a stated reason is not an acceptable control.

**Agenda 2063**

- **Aspiration 1** — a prosperous Africa based on inclusive growth and
  sustainable development, including **Goal 1** (a high standard of living and
  well-being) and **Goal 4** (transformed economies).
- Digital financial inclusion is part of that growth path: mobile-money rails
  that people trust, with controls that do not treat the unbanked as suspicious
  by default.

UNECA’s African AI Innovators track is the audience. The claim on the table is
a reproducible demo with a written limit, not a production AML or credit-bureau
system.

## Layout

```
app/                     FastAPI app, simulator, training, scoring
  main.py                GET /health, POST /score
  train.py               python -m app.train
examples/                curl payloads (synthetic)
models/                  joblib pipeline + metadata.json
tests/test_score.py      /score and /health checks
data/Real estate.csv     Week 1 lab only (preserved)
notebooks/               Week 1 walkthrough (preserved)
src/baseline_pipeline.py Week 1 regression baseline (preserved)
```

## Week 1 lab (preserved)

Applied Machine Learning, MSc Data Science & Analytics (Strathmore University).
DSA 8401, Week 1: an end-to-end **baseline**.

The lab walks the ML lifecycle once on a small public dataset. The goal is not
a clever model. It is a **leak-free baseline** that later techniques have to beat.

### Problem framing

Given a property's characteristics, predict its **price per unit area**. This is
supervised **regression**. The baseline to beat is "always predict the mean
price" (`DummyRegressor`).

The Week 1 lecture tells a credit-scoring story. This lab’s dataset is the real
estate valuation set: same lifecycle, different target (regression, not
classification). The showcase fraud-flag API above is the classification
product; it does not replace this baseline.

### Run the baseline

```bash
python src/baseline_pipeline.py
```

This loads the data, splits it (test set touched once), fits a mean baseline and
a scaled linear regression inside a leak-free `Pipeline`, cross-validates on the
training data, and reports lift over the baseline.

### Disciplines

1. Split before fitting anything; the test set is sacred.
2. Learn preprocessing inside the pipeline, on training folds only.
3. Ship a baseline first and report lift, never a raw score alone.
4. Cross-validate on train; keep the test set sealed until the end.

## License of the claims

Course lab material stays in-tree. The fraud-flag layer is a student showcase
prototype by Christopher Nguu Kioko for UNECA African AI Innovators. It is not
an offer of a regulated scoring service.
