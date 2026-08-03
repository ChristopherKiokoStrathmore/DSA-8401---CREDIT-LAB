# DSA 8401 - Week 1 Lab: End-to-End Baseline

Applied Machine Learning, MSc Data Science & Analytics (Strathmore University).

This repository walks the Week-1 ML lifecycle **once** on a small, honest,
real-world dataset. The goal is not a clever model. It is a **leak-free
baseline** that every technique in the rest of the course has to beat.

## Problem framing

Given a property's characteristics, predict its **price per unit area**. This is
supervised **regression** with a continuous target. The baseline to beat is
"always predict the mean price" (`DummyRegressor`); any real model must reduce
error below that floor to justify its existence.

> Note: the Week-1 lecture tells a *credit-scoring* story, but this lab's dataset
> is the Real estate valuation set. Same lifecycle, different target type
> (regression vs classification).

## Structure

```
DSA-8401-Credit-Lab/
  data/                 Real estate.csv  (the dataset)
  notebooks/            AML_Week_1.ipynb (exploratory, full walkthrough)
  src/                  baseline_pipeline.py (runnable script version)
  requirements.txt      pinned-ish environment
  .gitignore            keeps venv/ and caches out of the repo
  README.md             this file
```

## Setup

```bash
# 1. Create and activate an isolated environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Lock exact versions for reproducibility
pip freeze > requirements.txt
```

## Run the baseline

```bash
python src/baseline_pipeline.py
```

This loads the data, splits it honestly (test set touched once), fits a
mean baseline and a scaled linear regression inside a leak-free `Pipeline`,
cross-validates on the training data, and reports **lift over baseline**.

## The Week-1 disciplines this repo demonstrates

1. Split before fitting anything; the test set is sacred.
2. Learn all preprocessing (scaling) inside the Pipeline, on training folds only.
3. Always ship a baseline first and report lift, never a raw score alone.
4. Cross-validate on train; keep the test set sealed until the end.

## Submission

Push to GitHub and submit the repository link at the Week 1 submission point.

```bash
git add .
git commit -m "Week 1 baseline pipeline"
git branch -M main
git remote add origin https://github.com/<your-username>/DSA-8401-Credit-Lab.git
git push -u origin main
```
