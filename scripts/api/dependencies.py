"""Singleton model loaders used as FastAPI dependencies.

Each ``get_*`` function is decorated with ``lru_cache(maxsize=1)`` so the
expensive setup (training the intent classifier, loading sentence-transformers,
building the FAISS index) happens exactly once per process.
"""

import os
import sys
from functools import lru_cache

import pandas as pd

# Make `scripts.*` importable when uvicorn launches this module
_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BASE not in sys.path:
    sys.path.append(_BASE)

from scripts.compliance.compliance_checker import ComplianceChecker
from scripts.engine.entity_extractor import EntityExtractor
from scripts.engine.intent_classifier import IntentClassifier
from scripts.engine.listing_summarizer import ListingSummarizer
from scripts.engine.signal_extractor import SignalExtractor
from scripts.search.query_parser import QueryParser, SchemaValidator
from scripts.search.semantic_search import SemanticSearcher
from scripts.utils.paths import (
    EXTRACTION_CSV,
    FAISS_INDEX_BIN,
    INDEXED_LISTINGS_JSON,
    SCHEMA_JSON,
    TAXONOMY_JSON,
    ensure_dirs,
)


@lru_cache(maxsize=1)
def get_entity_extractor() -> EntityExtractor:
    return EntityExtractor(taxonomy_path=TAXONOMY_JSON)


@lru_cache(maxsize=1)
def get_signal_extractor() -> SignalExtractor:
    return SignalExtractor(taxonomy_path=TAXONOMY_JSON, entity_extractor=get_entity_extractor())


@lru_cache(maxsize=1)
def get_summarizer() -> ListingSummarizer:
    return ListingSummarizer(num_sentences=2)


@lru_cache(maxsize=1)
def get_compliance_checker() -> ComplianceChecker:
    return ComplianceChecker()


@lru_cache(maxsize=1)
def get_query_parser() -> QueryParser:
    """QueryParser auto-trains its embedded IntentClassifier on init."""
    return QueryParser()


@lru_cache(maxsize=1)
def get_intent_classifier() -> IntentClassifier:
    """Reuse the classifier already trained by QueryParser."""
    return get_query_parser()._clf


@lru_cache(maxsize=1)
def get_schema_validator() -> SchemaValidator:
    return SchemaValidator(schema_path=SCHEMA_JSON)


@lru_cache(maxsize=1)
def get_searcher() -> SemanticSearcher:
    """
    Load the FAISS index from disk if available, otherwise build it from
    extraction_results.csv and persist for next time.
    """
    ensure_dirs()
    searcher = SemanticSearcher()

    if os.path.exists(FAISS_INDEX_BIN) and os.path.exists(INDEXED_LISTINGS_JSON):
        searcher.load_index(FAISS_INDEX_BIN, INDEXED_LISTINGS_JSON)
        return searcher

    if not os.path.exists(EXTRACTION_CSV):
        raise FileNotFoundError(
            f"Cannot bootstrap semantic searcher: {EXTRACTION_CSV} not found. "
            f"Run scripts/pipelines/run_extraction.py first."
        )

    print(f"FAISS artifacts missing — building index from {EXTRACTION_CSV}...")
    df = pd.read_csv(EXTRACTION_CSV)
    remarks = df["remarks"].dropna().astype(str).tolist()
    searcher.build_index(remarks)
    searcher.save_index(FAISS_INDEX_BIN, INDEXED_LISTINGS_JSON)
    return searcher


def warmup_all() -> dict:
    """Initialize every singleton. Called from FastAPI lifespan startup."""
    status = {}
    for name, getter in [
        ("entity_extractor", get_entity_extractor),
        ("signal_extractor", get_signal_extractor),
        ("summarizer", get_summarizer),
        ("compliance_checker", get_compliance_checker),
        ("query_parser", get_query_parser),
        ("schema_validator", get_schema_validator),
        ("semantic_searcher", get_searcher),
    ]:
        try:
            getter()
            status[name] = "ready"
        except Exception as exc:
            status[name] = f"unavailable: {exc.__class__.__name__}: {exc}"
    return status
