"""Real Estate NLP API — Week 10 deliverable.

Exposes every component built across weeks 1-9 as a REST endpoint:

  GET  /                  → API metadata
  GET  /health            → liveness / component readiness
  POST /search            → semantic search w/ intent gating + filter extraction
  POST /parse-query       → parser only (intent + filters + SQL)
  POST /classify-intent   → intent classifier only
  POST /extract-entities  → regex entity extraction from free text
  POST /extract-signals   → full signal extraction from a listing record
  POST /summarize         → extractive summary
  POST /check-compliance  → Fair Housing compliance check

Globals:
  - Rate limit: 10 req/sec/IP (slowapi)
  - Cache: in-memory TTLCache (1h TTL, 1024 entries)
  - CORS: open (tighten in production)

Run locally:
  uvicorn scripts.api.main:app --reload --port 8000
  → http://localhost:8000/docs for the auto-generated OpenAPI UI
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from scripts.api import cache
from scripts.api.dependencies import (
    get_compliance_checker,
    get_entity_extractor,
    get_intent_classifier,
    get_query_parser,
    get_schema_validator,
    get_searcher,
    get_signal_extractor,
    get_summarizer,
    warmup_all,
)
from scripts.api.models import (
    ComplianceRequest,
    ComplianceResponse,
    EntitiesPayload,
    ExtractEntitiesRequest,
    ExtractEntitiesResponse,
    ExtractSignalsRequest,
    ExtractSignalsResponse,
    HealthResponse,
    IntentRequest,
    IntentResponse,
    ParseQueryRequest,
    ParseQueryResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SummarizeRequest,
    SummarizeResponse,
)
from scripts.compliance.compliance_checker import ComplianceChecker
from scripts.engine.entity_extractor import EntityExtractor
from scripts.engine.intent_classifier import IntentClassifier
from scripts.engine.listing_summarizer import ListingSummarizer
from scripts.engine.signal_extractor import SignalExtractor
from scripts.search.query_parser import QueryParser, SchemaValidator
from scripts.search.semantic_search import SemanticSearcher

API_VERSION = "1.0.0"

# slowapi: per-IP rate limiter. The default applies to every route.
limiter = Limiter(key_func=get_remote_address, default_limits=["10/second"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up everything except the FAISS searcher (which can be slow to build
    # on first run). Search calls will trigger lazy load on demand.
    print("Warming up models...")
    app.state.warmup_status = {}
    for getter, name in [
        (get_entity_extractor, "entity_extractor"),
        (get_signal_extractor, "signal_extractor"),
        (get_summarizer, "summarizer"),
        (get_compliance_checker, "compliance_checker"),
        (get_query_parser, "query_parser"),
        (get_schema_validator, "schema_validator"),
    ]:
        try:
            getter()
            app.state.warmup_status[name] = "ready"
        except Exception as exc:
            app.state.warmup_status[name] = f"unavailable: {exc.__class__.__name__}"
    app.state.warmup_status["semantic_searcher"] = "lazy"
    print("Warmup complete:", app.state.warmup_status)
    yield


app = FastAPI(
    title="Real Estate NLP API",
    description="REST interface for the IDX Exchange real-estate NLP pipeline.",
    version=API_VERSION,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


# ── Root + health ──────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "Real Estate NLP API",
        "version": API_VERSION,
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/search",
            "/parse-query",
            "/classify-intent",
            "/extract-entities",
            "/extract-signals",
            "/summarize",
            "/check-compliance",
        ],
    }


@app.get("/health", response_model=HealthResponse)
def health(request: Request):
    components = getattr(request.app.state, "warmup_status", {})
    overall = "ok" if all(v in ("ready", "lazy") for v in components.values()) else "degraded"
    return HealthResponse(status=overall, components=components, version=API_VERSION)


# ── Parse query ────────────────────────────────────────────────────────────
@app.post("/parse-query", response_model=ParseQueryResponse)
def parse_query(
    request: Request,
    body: ParseQueryRequest,
    parser: QueryParser = Depends(get_query_parser),
    validator: SchemaValidator = Depends(get_schema_validator),
):
    key = cache.cache_key("parse-query", body.query)

    def _do() -> dict:
        parsed = parser.parse(body.query)
        out = {
            "query": body.query,
            "intent": parsed["intent"],
            "confidence": parsed["confidence"],
            "sql_ready": parsed["sql_ready"],
            "filters": parsed["filters"],
            "message": parsed["message"],
            "schema_errors": [],
            "sql": None,
            "params": None,
        }
        if parsed["sql_ready"] and parsed["filters"]:
            ok, errors = validator.validate(parsed["filters"])
            out["schema_errors"] = errors
            if ok:
                sql, params = parser.to_sql(parsed["filters"])
                out["sql"] = sql
                out["params"] = list(params)
        return out

    result, was_cached = cache.get_or_compute(key, _do)
    return ParseQueryResponse(**result, cached=was_cached)


# ── Classify intent ────────────────────────────────────────────────────────
@app.post("/classify-intent", response_model=IntentResponse)
def classify_intent(
    request: Request,
    body: IntentRequest,
    clf: IntentClassifier = Depends(get_intent_classifier),
):
    key = cache.cache_key("intent", body.query)

    def _do() -> dict:
        intent, confidence = clf.predict(body.query)
        return {
            "query": body.query,
            "intent": intent,
            "confidence": round(confidence, 4),
        }

    result, was_cached = cache.get_or_compute(key, _do)
    return IntentResponse(**result, cached=was_cached)


# ── Extract entities ───────────────────────────────────────────────────────
@app.post("/extract-entities", response_model=ExtractEntitiesResponse)
def extract_entities(
    request: Request,
    body: ExtractEntitiesRequest,
    extractor: EntityExtractor = Depends(get_entity_extractor),
):
    key = cache.cache_key("entities", body.text)

    def _do() -> dict:
        ents = extractor.extract_all(body.text)
        return {"text": body.text, "entities": ents}

    result, was_cached = cache.get_or_compute(key, _do)
    return ExtractEntitiesResponse(
        text=result["text"],
        entities=EntitiesPayload(**result["entities"]),
        cached=was_cached,
    )


# ── Extract signals ────────────────────────────────────────────────────────
@app.post("/extract-signals", response_model=ExtractSignalsResponse)
def extract_signals(
    request: Request,
    body: ExtractSignalsRequest,
    extractor: SignalExtractor = Depends(get_signal_extractor),
):
    # No caching — listing dicts are arbitrary and may not be JSON-stable
    signals = extractor.extract_signals(body.listing)
    return ExtractSignalsResponse(
        listing_id=signals.get("listing_id"),
        entities=EntitiesPayload(**signals.get("entities", {})),
        amenities=signals.get("amenities", []),
        condition_keywords=signals.get("condition_keywords", []),
        financing_terms=signals.get("financing_terms", []),
        location_features=signals.get("location_features", []),
    )


# ── Summarize ──────────────────────────────────────────────────────────────
@app.post("/summarize", response_model=SummarizeResponse)
def summarize(
    request: Request,
    body: SummarizeRequest,
    summarizer: ListingSummarizer = Depends(get_summarizer),
    extractor: EntityExtractor = Depends(get_entity_extractor),
):
    # Cache key includes num_sentences and a short prefix of the entities for stability
    ent_dict = body.entities.model_dump() if body.entities else None
    key = cache.cache_key("summarize", body.num_sentences, body.remarks, str(ent_dict))

    def _do() -> dict:
        ents = ent_dict if ent_dict is not None else extractor.extract_all(body.remarks)
        summary = summarizer.extractive_summary(body.remarks, ents, num_sentences=body.num_sentences)
        return {"summary": summary, "num_sentences": body.num_sentences}

    result, was_cached = cache.get_or_compute(key, _do)
    return SummarizeResponse(**result, cached=was_cached)


# ── Compliance ─────────────────────────────────────────────────────────────
@app.post("/check-compliance", response_model=ComplianceResponse)
def check_compliance(
    request: Request,
    body: ComplianceRequest,
    checker: ComplianceChecker = Depends(get_compliance_checker),
):
    key = cache.cache_key("compliance", body.text)

    def _do() -> dict:
        return checker.check_listing(body.text)

    result, was_cached = cache.get_or_compute(key, _do)
    return ComplianceResponse(**result, cached=was_cached)


# ── Search (full pipeline) ─────────────────────────────────────────────────
@app.post("/search", response_model=SearchResponse)
def search(
    request: Request,
    body: SearchRequest,
    parser: QueryParser = Depends(get_query_parser),
    validator: SchemaValidator = Depends(get_schema_validator),
):
    key = cache.cache_key("search", body.top_k, body.query)

    def _do() -> dict:
        parsed = parser.parse(body.query)
        out = {
            "query": body.query,
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
        }

        if parsed["sql_ready"] and parsed["filters"]:
            ok, errors = validator.validate(parsed["filters"])
            out["schema_errors"] = errors
            if ok:
                sql, params = parser.to_sql(parsed["filters"])
                out["sql"] = sql
                out["params"] = list(params)

        # Run semantic search regardless of intent — even researching/browsing users
        # benefit from seeing relevant listings as supporting context
        try:
            searcher: SemanticSearcher = get_searcher()
            hits = searcher.search(body.query, top_k=body.top_k)
            out["results"] = [
                {"rank": i + 1, "score": float(score), "remarks": text}
                for i, (text, score) in enumerate(hits)
                if not text.startswith("Error:")  # SemanticSearcher's not-built sentinel
            ]
            out["count"] = len(out["results"])
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

        return out

    result, was_cached = cache.get_or_compute(key, _do)
    items = [SearchResultItem(**r) for r in result["results"]]
    return SearchResponse(
        query=result["query"],
        intent=result["intent"],
        confidence=result["confidence"],
        sql_ready=result["sql_ready"],
        filters=result["filters"],
        sql=result.get("sql"),
        params=result.get("params"),
        schema_errors=result["schema_errors"],
        message=result["message"],
        results=items,
        count=result["count"],
        cached=was_cached,
    )


# ── Cache management (handy for demos) ─────────────────────────────────────
@app.get("/cache/stats")
def cache_stats(request: Request):
    return cache.stats()


@app.post("/cache/clear")
def cache_clear(request: Request):
    cache.clear()
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("scripts.api.main:app", host="0.0.0.0", port=8000, reload=True)
