"""Thin client for the Real Estate NLP API used by the Streamlit demo.

Every call returns ``(response_json, latency_ms)`` so the UI can render
per-request timing without measuring inside each Streamlit page.

The base URL is taken from the ``API_BASE_URL`` env var (default
``http://localhost:8000``) so the same app can point at a local uvicorn or
a hosted Render deployment without code changes.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Tuple

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
DEFAULT_TIMEOUT = 30


class APIError(Exception):
    """Raised when the API is unreachable or returns a non-2xx response."""


def _request(method: str, path: str, *, json: Dict[str, Any] | None = None,
             timeout: int = DEFAULT_TIMEOUT) -> Tuple[Dict[str, Any], float]:
    url = f"{API_BASE_URL}{path}"
    t0 = time.perf_counter()
    try:
        r = requests.request(method, url, json=json, timeout=timeout)
    except requests.RequestException as exc:
        raise APIError(f"Network error calling {path}: {exc}") from exc
    latency_ms = (time.perf_counter() - t0) * 1000
    if not r.ok:
        raise APIError(f"{path} returned {r.status_code}: {r.text[:200]}")
    return r.json(), latency_ms


def health() -> Tuple[Dict[str, Any], float]:
    return _request("GET", "/health", timeout=10)


def parse_query(query: str) -> Tuple[Dict[str, Any], float]:
    return _request("POST", "/parse-query", json={"query": query})


def search(query: str, top_k: int = 10) -> Tuple[Dict[str, Any], float]:
    # First /search after cold start triggers FAISS load + index build — allow extra time
    return _request("POST", "/search", json={"query": query, "top_k": top_k}, timeout=120)


def search_keyword(query: str, top_k: int = 10) -> Tuple[Dict[str, Any], float]:
    return _request("POST", "/search-keyword", json={"query": query, "top_k": top_k})


def summarize(remarks: str, num_sentences: int = 2) -> Tuple[Dict[str, Any], float]:
    return _request("POST", "/summarize", json={"remarks": remarks, "num_sentences": num_sentences})


def check_compliance(text: str) -> Tuple[Dict[str, Any], float]:
    return _request("POST", "/check-compliance", json={"text": text})


def search_both(query: str, top_k: int = 10) -> Dict[str, Tuple[Dict[str, Any], float]]:
    """Fire /search and /search-keyword in parallel so the side-by-side latency
    comparison reflects actual server time, not sequential client overhead.

    Returns {"semantic": (json, ms), "keyword": (json, ms)}. Either entry may
    be replaced with an APIError instance if that call failed independently.
    """
    with ThreadPoolExecutor(max_workers=2) as pool:
        sem_fut = pool.submit(search, query, top_k)
        kw_fut = pool.submit(search_keyword, query, top_k)
        out: Dict[str, Any] = {}
        for name, fut in [("semantic", sem_fut), ("keyword", kw_fut)]:
            try:
                out[name] = fut.result()
            except APIError as exc:
                out[name] = exc
    return out
