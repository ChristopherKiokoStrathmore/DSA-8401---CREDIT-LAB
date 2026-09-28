# Public demo image for the Nairobi Fintech Fraud Flag API.
# Listens on $PORT (default 7860, the Hugging Face Docker Space port).
# Render's free web service injects PORT and needs no secrets.
# Hugging Face Docker Spaces run the container as uid 1000.

FROM python:3.11-slim

RUN useradd --create-home --uid 1000 user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR $HOME/app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user app ./app
COPY --chown=user examples ./examples
COPY --chown=user models ./models

USER user
EXPOSE 7860

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
