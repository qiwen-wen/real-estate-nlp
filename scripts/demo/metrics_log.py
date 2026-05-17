"""Append-only JSONL log of demo searches and ratings.

Two files in ``results/``:
  - ``demo_queries.jsonl``  — one record per executed search
  - ``demo_ratings.jsonl``  — one record per thumbs up/down

JSONL keeps the writer simple (append-and-flush, no schema migration) and the
reader trivial (line-by-line ``json.loads``).
"""

import json
import os
from typing import Any, Dict, Iterator, List

from scripts.utils.paths import RESULTS, ensure_dirs

SEARCHES_LOG = os.path.join(RESULTS, "demo_queries.jsonl")
RATINGS_LOG = os.path.join(RESULTS, "demo_ratings.jsonl")


def _append(path: str, record: Dict[str, Any]) -> None:
    ensure_dirs()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def append_search(record: Dict[str, Any]) -> None:
    _append(SEARCHES_LOG, record)


def append_rating(record: Dict[str, Any]) -> None:
    _append(RATINGS_LOG, record)


def _iter_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_searches() -> List[Dict[str, Any]]:
    return list(_iter_jsonl(SEARCHES_LOG))


def read_ratings() -> List[Dict[str, Any]]:
    return list(_iter_jsonl(RATINGS_LOG))
