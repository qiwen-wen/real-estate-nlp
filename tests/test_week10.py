"""Week 10 — FastAPI integration tests.

Uses FastAPI's TestClient (which spins up the app in-process). The /search
endpoint is skipped by default because it triggers a FAISS build on first
call, which is too slow for a unit-test loop. Mark it for opt-in:

    pytest tests/test_week10.py -m search
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from scripts.api.main import app
from scripts.api import cache as api_cache


@pytest.fixture(scope="module")
def client():
    # Context manager triggers FastAPI lifespan (warmup)
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _clear_cache():
    api_cache.clear()
    yield


# ── Root + health ──────────────────────────────────────────────────────────
def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Real Estate NLP API"
    assert "/search" in body["endpoints"]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    # Every non-search component must be ready after warmup
    for name in ("entity_extractor", "summarizer", "compliance_checker", "query_parser"):
        assert body["components"].get(name) == "ready", body["components"]


# ── Parse query ────────────────────────────────────────────────────────────
def test_parse_ready_to_buy(client):
    r = client.post("/parse-query", json={"query": "3 bed 2 bath under 700k in Irvine"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "ready_to_buy"
    assert body["sql_ready"] is True
    assert body["filters"]["bedrooms"] == 3
    assert body["filters"]["price_max"] == 700_000
    assert body["filters"]["city"].strip().lower() == "irvine"
    # Schema validation should accept Irvine + 700k
    assert body["schema_errors"] == []
    assert body["sql"].startswith("SELECT * FROM rets_property WHERE")


def test_parse_browsing(client):
    r = client.post("/parse-query", json={"query": "just looking for now"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "browsing"
    assert body["sql_ready"] is False
    assert body["sql"] is None


def test_parse_invalid_city_flagged(client):
    r = client.post("/parse-query", json={"query": "3 bed under 500k in Atlantis"})
    assert r.status_code == 200
    body = r.json()
    if body["sql_ready"]:
        # Atlantis is not a real California city — schema validator should flag it
        assert any("Atlantis" in e for e in body["schema_errors"])
        assert body["sql"] is None  # blocked because validation failed


def test_parse_caching(client):
    q = {"query": "show me homes"}
    r1 = client.post("/parse-query", json=q)
    r2 = client.post("/parse-query", json=q)
    assert r1.json()["cached"] is False
    assert r2.json()["cached"] is True


def test_parse_validation_error(client):
    r = client.post("/parse-query", json={"query": ""})
    assert r.status_code == 422  # pydantic min_length=1


# ── Intent classifier ──────────────────────────────────────────────────────
def test_classify_intent(client):
    r = client.post("/classify-intent", json={"query": "what are typical HOA fees"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "researching"
    assert 0.0 <= body["confidence"] <= 1.0


# ── Entities ───────────────────────────────────────────────────────────────
def test_extract_entities(client):
    text = "Beautiful 3 bed 2 bath home, 1,800 sqft, $750,000 with pool and granite counters"
    r = client.post("/extract-entities", json={"text": text})
    assert r.status_code == 200
    ents = r.json()["entities"]
    assert ents["bedrooms"] == 3
    assert ents["bathrooms"] == 2.0
    assert ents["sqft"] == 1800
    assert ents["price"] == 750_000


# ── Signals ────────────────────────────────────────────────────────────────
def test_extract_signals(client):
    listing = {
        "L_ListingID": "TEST-1",
        "L_Remarks": "Stunning 4 bed 3 bath with mountain views and gourmet kitchen",
        "L_Keyword2": 4,
        "LM_Dec_3": 3,
        "L_SystemPrice": 1_200_000,
        "LM_Int2_3": 2500,
    }
    r = client.post("/extract-signals", json={"listing": listing})
    assert r.status_code == 200
    body = r.json()
    assert body["listing_id"] == "TEST-1"
    assert body["entities"]["bedrooms"] == 4
    assert body["entities"]["price"] == 1_200_000


# ── Summarize ──────────────────────────────────────────────────────────────
def test_summarize_returns_subset(client):
    remarks = (
        "Beautiful 3 bedroom home in Irvine. Updated kitchen with granite countertops. "
        "Master suite features walk-in closet. Backyard with pool and spa. "
        "Two car garage. Close to schools."
    )
    r = client.post("/summarize", json={"remarks": remarks, "num_sentences": 2})
    assert r.status_code == 200
    summary = r.json()["summary"]
    assert summary  # non-empty
    assert len(summary) < len(remarks)


# ── Compliance ─────────────────────────────────────────────────────────────
def test_compliance_violation(client):
    r = client.post(
        "/check-compliance",
        json={"text": "Beautiful 2BR, no children allowed. Adults only community."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["compliant"] is False
    assert body["error_count"] >= 2
    categories = {v["category"] for v in body["violations"]}
    assert "familial_status" in categories


def test_compliance_clean_listing(client):
    r = client.post(
        "/check-compliance",
        json={"text": "Charming 2BR with hardwood floors, in-unit laundry, walk-in closet."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["compliant"] is True
    assert body["error_count"] == 0


def test_compliance_allowlist(client):
    """'wheelchair' alone might trip a future pattern, but 'wheelchair accessible' must not."""
    r = client.post(
        "/check-compliance",
        json={"text": "Wheelchair accessible unit with roll-in shower. Equal housing opportunity."},
    )
    assert r.status_code == 200
    assert r.json()["compliant"] is True


# ── Cache management ───────────────────────────────────────────────────────
def test_cache_stats_and_clear(client):
    client.post("/check-compliance", json={"text": "Hardwood floors throughout."})
    s1 = client.get("/cache/stats").json()
    assert s1["size"] >= 1
    client.post("/cache/clear")
    s2 = client.get("/cache/stats").json()
    assert s2["size"] == 0


# ── OpenAPI ────────────────────────────────────────────────────────────────
def test_openapi_docs_available(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    paths = set(spec["paths"].keys())
    for required in ("/search", "/parse-query", "/extract-entities",
                     "/summarize", "/check-compliance", "/health",
                     "/extract-signals", "/classify-intent"):
        assert required in paths, f"Missing endpoint in OpenAPI spec: {required}"


# ── Search (opt-in; slow first run) ────────────────────────────────────────
@pytest.mark.search
def test_search_returns_results(client):
    r = client.post("/search", json={"query": "modern kitchen with granite", "top_k": 3})
    assert r.status_code == 200
    body = r.json()
    assert "intent" in body
    assert isinstance(body["results"], list)
    assert body["count"] == len(body["results"])
