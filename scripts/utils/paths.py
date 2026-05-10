import os

# Project root — always points to real-estate-nlp/
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Input paths (data sources, never changes) ──────────────────────────────
DATA_RAW        = os.path.join(ROOT, 'data', 'raw')
DATA_INTERIM    = os.path.join(ROOT, 'data', 'interim')
DATA_PROCESSED  = os.path.join(ROOT, 'data', 'processed')
DATA_MODELS     = os.path.join(ROOT, 'data', 'models')

# Specific input files
SQL_FILE        = os.path.join(DATA_RAW,       'rets_property.sql')
CLEANED_CSV     = os.path.join(DATA_PROCESSED, 'cleaned_listings.csv')
TAXONOMY_JSON   = os.path.join(DATA_PROCESSED, 'taxonomy.json')
SCHEMA_JSON     = os.path.join(DATA_PROCESSED, 'schema.json')

# Interim files
LISTING_SAMPLE      = os.path.join(DATA_INTERIM, 'listing_sample.csv')
VALIDATION_SAMPLE   = os.path.join(DATA_INTERIM, 'validation_sample.csv')

# ── Output paths (results folder) ──────────────────────────────────────────
RESULTS             = os.path.join(ROOT, 'results')

EXTRACTION_CSV      = os.path.join(RESULTS, 'extraction_results.csv')
SIGNALS_JSON        = os.path.join(RESULTS, 'extracted_signals.json')
SEARCH_EVAL_CSV     = os.path.join(RESULTS, 'search_evaluation_results.csv')
RELEVANCE_JSON      = os.path.join(RESULTS, 'relevance_eval_50_pairs_notebook.json')
INTENT_JSON         = os.path.join(RESULTS, 'intent_classifier_metrics.json')

# FAISS artifacts (built by scripts/pipelines/build_search_index.py, loaded by the API)
FAISS_INDEX_BIN       = os.path.join(DATA_MODELS, 'faiss_index.bin')
INDEXED_LISTINGS_JSON = os.path.join(DATA_MODELS, 'indexed_listings.json')

def ensure_dirs():
    """Call this at the start of any pipeline to make sure all folders exist."""
    for path in [DATA_RAW, DATA_INTERIM, DATA_PROCESSED, DATA_MODELS, RESULTS]:
        os.makedirs(path, exist_ok=True)