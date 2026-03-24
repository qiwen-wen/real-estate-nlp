# Scripts Folder Guide

This folder contains the project's data processing and NLP pipeline scripts.

## Folder-to-file mapping

### `scripts/data_loading`
- `__init__.py`: Declares package exports for loading-related modules.
- `data_loading.py`: Pulls sample listings from MySQL and writes `data/processed/listing_sample.csv`.
- `meaningful_taxonomy_json_builder.py`: Builds a curated taxonomy and writes `data/processed/taxonomy.json`.

### `scripts/data_cleaner`
- `__init__.py`: Exposes `TextCleaner` for cleaner package imports.
- `text_cleaning.py`: Defines `TextCleaner` for text normalization and profiling.

### `scripts/data_extractor`
- `__init__.py`: Declares extractor submodule exports for package-level discovery.
- `entity_extractor.py`: Defines `EntityExtractor` for field extraction and span extraction.
- `run_extractor.py`: Runs extraction pipeline and writes `data/processed/data_prediction.jsonl`.
- `evaluate_entity.py`: Evaluates predicted spans against gold labels from JSONL files.
- `query_generation.py`: Generates synthetic query samples and writes `data/processed/user_queries.json`.
- `taxonomy_builder.py`: Builds frequency-based taxonomy terms from listing remarks.

### `scripts/query_parser`
- `query_parser.py`: Defines `QueryParser` for query normalization, tokenization, and parsing.
- `__init__.py`: Exposes `QueryParser` package import.

### `scripts` (root package)
- `__init__.py`: Declares top-level subpackages (`data_loading`, `data_cleaner`, `data_extractor`, `query_parser`).

## Path and import notes

- Package-style imports now follow the current folder structure, for example:
  - `scripts.data_extractor.entity_extractor`
  - `scripts.data_loading.meaningful_taxonomy_json_builder`
- Evaluation input/output paths use JSONL consistently:
  - `data/processed/data_template.jsonl`
  - `data/processed/data_prediction.jsonl`

## Recommended run commands (from project root)

```bash
python3 -m scripts.data_extractor.run_extractor
python3 -m scripts.data_extractor.evaluate_entity
```

## Convenient import patterns

```python
from scripts import TextCleaner, QueryParser, EntityExtractor
from scripts.data_cleaner import TextCleaner
from scripts.query_parser import QueryParser
from scripts.data_extractor import EntityExtractor, evaluate
```

Note: modules under `scripts/data_loading` and some generator scripts are execution-oriented.
Avoid importing them in `__init__.py` exports because import may trigger DB access or file writes.
