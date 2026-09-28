"""Nairobi Fintech Fraud Flag API.

    uvicorn app.main:app --host 127.0.0.1 --port 8000
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.demo import render_demo_page
from app.features import DISCLAIMER, MODEL_VERSION, PRODUCT_NAME
from app.schemas import HealthResponse, ScoreRequest, ScoreResponse
from app.scoring import get_scorer

app = FastAPI(
    title=PRODUCT_NAME,
    version=MODEL_VERSION,
    summary="Synthetic mobile-money fraud flag for a UNECA showcase.",
    description=(
        "Scores one wallet from behavioural and thin-file aggregates. "
        "Training rows are synthetic. The score is a demonstration probability, "
        "a risk band, and up to three short reasons. "
        "A browser demo of the same score is served at / . "
        + DISCLAIMER
    ),
)


@app.get("/", include_in_schema=False)
@app.get("/demo", include_in_schema=False)
def demo_page() -> HTMLResponse:
    return HTMLResponse(render_demo_page())


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    scorer = get_scorer()
    return HealthResponse(
        status="ok",
        product=PRODUCT_NAME,
        model_version=scorer.model_version,
        data_policy="synthetic aggregates only; no PII accepted or stored",
    )


@app.post("/score", response_model=ScoreResponse)
def score(payload: ScoreRequest) -> ScoreResponse:
    return get_scorer().score(payload)
