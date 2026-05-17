"""In-process backend for the Streamlit demo.

Originally an HTTP client for the FastAPI service in `scripts.api.main`.
Pivoted to in-process function calls because the full stack
(torch + sentence-transformers + faiss + scikit-learn) cannot fit in
Render's 512 MB free-tier RAM. Streamlit Cloud has 1 GB and runs the
work in the same process — no second service required.

Public surface (function signatures and return shapes) is preserved
identically to the HTTP version, so ``app.py`` and ``pages/1_metrics.py``
don't need to change. Each call still returns ``(payload_dict, latency_ms)``.

The FastAPI app in `scripts/api/main.py` is **not** deleted — it's still the
Week 10 deliverable and runs locally with ``uvicorn`` for `/docs`-style demos.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Tuple

# `streamlit run` invokes the parent app.py as a top-level script; this file
# is then imported relatively. Make sure the project root is on sys.path so
# `scripts.api.dependencies` resolves regardless of CWD.
_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BASE not in sys.path:
    sys.path.append(_BASE)

from scripts.api.dependencies import (
    get_bm25_searcher,
    get_compliance_checker,
    get_entity_extractor,
    get_query_parser,
    get_schema_validator,
    get_searcher,
    get_summarizer,
)

# Kept as a public constant because app.py displays it in the sidebar.
API_BASE_URL = "in-process (Streamlit Cloud)"


class APIError(Exception):
    """Raised when an in-process call fails. Same name as the HTTP version so
    `except api.APIError` in app.py / pages keeps working unchanged."""


def _timed(fn):
    """Wrap a callable so it returns ``(result, latency_ms)``."""
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            raise APIError(f"{fn.__name__} failed: {exc}") from exc
        latency_ms = (time.perf_counter() - t0) * 1000
        return result, latency_ms
    return wrapper


# ── Health ──────────────────────────────────────────────────────────────────
@_timed
def health() -> Dict[str, Any]:
    components: Dict[str, str] = {}
    for name, getter in [
        ("entity_extractor", get_entity_extractor),
        ("summarizer", get_summarizer),
        ("compliance_checker", get_compliance_checker),
        ("query_parser", get_query_parser),
        ("schema_validator", get_schema_validator),
        ("bm25_searcher", get_bm25_searcher),
    ]:
        try:
            getter()
            components[name] = "ready"
        except Exception as exc:
            components[name] = f"unavailable: {exc.__class__.__name__}"
    # Heavy semantic searcher stays lazy — first /search builds or loads it
    components["semantic_searcher"] = "lazy"
    overall = "ok" if all(v in ("ready", "lazy") for v in components.values()) else "degraded"
    return {"status": overall, "components": components, "version": "1.0.0-inproc"}


# ── Parse query ─────────────────────────────────────────────────────────────
@_timed
def parse_query(query: str) -> Dict[str, Any]:
    parser = get_query_parser()
    validator = get_schema_validator()
    parsed = parser.parse(query)
    out: Dict[str, Any] = {
        "query": query,
        "intent": parsed["intent"],
        "confidence": parsed["confidence"],
        "sql_ready": parsed["sql_ready"],
        "filters": parsed["filters"],
        "message": parsed["message"],
        "schema_errors": [],
        "sql": None,
        "params": None,
        "cached": False,
    }
    if parsed["sql_ready"] and parsed["filters"]:
        ok, errors = validator.validate(parsed["filters"])
        out["schema_errors"] = errors
        if ok:
            sql, params = parser.to_sql(parsed["filters"])
            out["sql"] = sql
            out["params"] = list(params)
    return out


# ── Semantic search ─────────────────────────────────────────────────────────
@_timed
def search(query: str, top_k: int = 10) -> Dict[str, Any]:
    parser = get_query_parser()
    validator = get_schema_validator()
    parsed = parser.parse(query)
    out: Dict[str, Any] = {
        "query": query,
        "intent": parsed["intent"],
        "confidence": parsed["confidence"],
        "sql_ready": parsed["sql_ready"],
        "filters": parsed["filters"],
        "message": parsed["message"],
        "schema_errors": [],
        "sql": None,
        "params": None,
        "results": [],
        "count": 0,
        "cached": False,
    }
    if parsed["sql_ready"] and parsed["filters"]:
        ok, errors = validator.validate(parsed["filters"])
        out["schema_errors"] = errors
        if ok:
            sql, params = parser.to_sql(parsed["filters"])
            out["sql"] = sql
            out["params"] = list(params)

    searcher = get_searcher()
    hits = searcher.search(query, top_k=top_k)
    out["results"] = [
        {"rank": i + 1, "score": float(score), "remarks": text}
        for i, (text, score) in enumerate(hits)
        if not text.startswith("Error:")
    ]
    out["count"] = len(out["results"])
    return out


# ── BM25 keyword search ─────────────────────────────────────────────────────
@_timed
def search_keyword(query: str, top_k: int = 10) -> Dict[str, Any]:
    bm25 = get_bm25_searcher()
    hits = bm25.search(query, top_k=top_k)
    results = []
    for i, hit in enumerate(hits):
        listing = hit["listing"]
        text = listing.get("remarks") if isinstance(listing, dict) else str(listing)
        results.append({
            "rank": i + 1,
            "score": float(hit["score"]),
            "remarks": text or "",
        })
    return {"query": query, "results": results, "count": len(results), "cached": False}


# ── Summarize ───────────────────────────────────────────────────────────────
@_timed
def summarize(remarks: str, num_sentences: int = 2) -> Dict[str, Any]:
    extractor = get_entity_extractor()
    summarizer = get_summarizer()
    ents = extractor.extract_all(remarks)
    summary = summarizer.extractive_summary(remarks, ents, num_sentences=num_sentences)
    return {"summary": summary, "num_sentences": num_sentences, "cached": False}


# ── Compliance ──────────────────────────────────────────────────────────────
@_timed
def check_compliance(text: str) -> Dict[str, Any]:
    checker = get_compliance_checker()
    result = checker.check_listing(text)
    result.setdefault("cached", False)
    return result


# ── Parallel both-search (used by the side-by-side comparison tab) ──────────
def search_both(query: str, top_k: int = 10) -> Dict[str, Any]:
    """Fire semantic and keyword searches in parallel threads.

    Returns ``{"semantic": (json, ms), "keyword": (json, ms)}``. Either entry
    may be replaced with an APIError instance if that individual call failed.
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
