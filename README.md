# 🏡 Real Estate Listing Intelligence System

> An end-to-end NLP pipeline for intelligent real estate search, built during a 12-week internship with **IDX Exchange**. Transforms unstructured MLS listing remarks and natural language queries into structured, searchable data — going beyond keyword filters to understand what buyers actually mean.

---

## 🔍 Overview

Traditional MLS search relies on rigid dropdown filters. This system understands natural language — parsing queries like *"3 bed under 700k in Irvine with a pool"* into structured filters, extracting entities from listing descriptions, and ranking results by semantic similarity rather than exact keyword match.

**Data:** Real MLS listings from three SQL tables (`rets_property`, `rets_openhouse`, `california_sold`) loaded via Docker/MySQL.

---

## 🏗️ What's Built

### 🎯 Buyer Intent Classification
Classifies user queries into `browsing`, `researching`, or `ready_to_buy` before any SQL is generated — routing queries intelligently based on what the user actually wants.

- Trained on 231 labeled real estate queries across 3 intent categories
- TF-IDF + Logistic Regression classifier achieving **100% test accuracy**
- Confidence scores on every prediction
- Integrated directly into the query parser — browsing and researching queries skip SQL entirely, ready-to-buy queries proceed to full filter extraction

```python
parser = QueryParser()
result = parser.parse("3 bed 2 bath under 700k in Irvine")
# → {'intent': 'ready_to_buy', 'confidence': 0.98, 'sql_ready': True,
#    'filters': {'bedrooms': 3, 'price_max': 700000, 'city': 'Irvine'}}
```

---

### 🔎 Natural Language Query Parser
Parses free-text queries into structured filters and safe parameterized SQL — no string concatenation, no injection risk.

- Handles price ranges (`under 500k`, `below $1m`), bedroom counts (`3 bed`, `2+ br`), city extraction, and **negation** (`no pool`, `without garage`)
- `SchemaValidator` cross-checks parsed filters against a real database schema — catches invalid cities and out-of-range prices before hitting SQL
- Generates clean `WHERE` clauses with `%s` parameterization

```python
sql, params = parser.to_sql(result['filters'])
# → "SELECT * FROM rets_property WHERE L_SystemPrice <= %s AND L_Keyword2 = %s AND L_City = %s"
```

---

### 🧠 Semantic Search (FAISS + sentence-transformers)
Encodes listing remarks into dense vector embeddings and builds a FAISS index for sub-100ms similarity search.

- Uses `all-MiniLM-L6-v2` (384-dim embeddings) with cosine similarity via normalized inner product
- **Local model caching** — downloads once, loads from disk on subsequent runs
- Compared against BM25 keyword baseline — results saved to `results/search_evaluation_results.csv`

```python
searcher = SemanticSearcher()
searcher.build_index(remarks_list)
results = searcher.search("open floor plan with mountain views", top_k=5)
```

---

### 🏠 Entity Extraction
Regex-based extractor pulling structured fields from free-text listing remarks.

- Extracts bedrooms, bathrooms, price, square footage, and amenities
- Amenity detection uses a **200+ term taxonomy** built from real listing language
- Handles edge cases: comma-separated numbers (`2,000 sqft`), decimal bathrooms (`2.5 ba`), hyphenated formats (`3-bed`)

---

### 📦 Signal Extraction
Combines entity extraction with taxonomy matching to produce structured JSON signals per listing.

- **Accuracy fallback**: if regex finds nothing in remarks, pulls directly from SQL columns (`L_Keyword2`, `LM_Dec_3`, `L_SystemPrice`) — ensuring no data is lost
- Categorizes taxonomy matches into amenities, condition keywords (`modern`, `renovated`), financing terms (`HOA`, `seller financing`), and location features (`canyon view`, `hillside`)
- Results saved to `results/extracted_signals.json`

```python
extractor = SignalExtractor()
signals = extractor.extract_signals(listing_record)
# → {entities, amenities, condition_keywords, financing_terms, location_features}
```

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-yellow?logo=huggingface)
![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-blue)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange?logo=scikit-learn)
![spaCy](https://img.shields.io/badge/spaCy-NLP-09a3d5)
![pytest](https://img.shields.io/badge/pytest-Tested-green?logo=pytest)

---

## 🔜 In Progress

- **Listing Summarization** — extractive summaries with ROUGE evaluation
- **Fair Housing Compliance Checker** — detecting prohibited language in listings
- **REST API** — FastAPI endpoints exposing all NLP capabilities
- **Streamlit Demo** — end-to-end natural language search interface

---

## 📌 Acknowledgements

- Built during a 12-week NLP internship with **IDX Exchange**
- Working with real MLS data from active California property listings

> ⚠️ Raw MLS data is not included in this repo as it contains proprietary IDX Exchange listing data.
