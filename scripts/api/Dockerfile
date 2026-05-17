# Real Estate NLP API container
# Build:  docker build -f scripts/api/Dockerfile -t idx-nlp-api .
# Run:    docker run -p 8000:8000 -v $(pwd)/data:/app/data -v $(pwd)/results:/app/results idx-nlp-api

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps: build tools for faiss/numpy wheels, libgomp for some sklearn ops
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# NLTK data (punkt for sentence tokenization in summarizer)
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)"

COPY scripts/ /app/scripts/
COPY data/processed/ /app/data/processed/
# Bake in the FAISS index if it exists at build time (skip silently if not)
COPY data/models/ /app/data/models/
COPY results/extraction_results.csv /app/results/extraction_results.csv

EXPOSE 8000

# Healthcheck pings /health every 30s. Honor $PORT for hosts (Render, Fly, etc.)
# that inject their own port; fall back to 8000 for local docker run.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8000}/health || exit 1

# Use JSON exec form with an explicit `sh -c` so `$PORT` is expanded at runtime
# (Render injects PORT=10000; the bare exec form does NOT perform env var
# substitution). Falls back to 8000 for `docker run` locally.
CMD ["sh", "-c", "uvicorn scripts.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
