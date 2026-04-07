"""Semantic search utilities for listing remarks.

Supports two common sentence-embedding sizes:
- 384 dims: sentence-transformers/all-MiniLM-L6-v2
- 768 dims: sentence-transformers/all-mpnet-base-v2
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MODEL_BY_DIM = {
    384: "sentence-transformers/all-MiniLM-L6-v2",
    768: "sentence-transformers/all-mpnet-base-v2",
}


@dataclass(frozen=True)
class SearchResult:
    remark: str
    score: float


@dataclass(frozen=True)
class SearchHit:
    index: int
    remark: str
    score: float


class SemanticSearcher:
    def __init__(self, embedding_dim: int = 384) -> None:
        if embedding_dim not in MODEL_BY_DIM:
            raise ValueError(f"embedding_dim must be one of {sorted(MODEL_BY_DIM)}")

        self.embedding_dim = embedding_dim
        self.model_name = MODEL_BY_DIM[embedding_dim]
        self._model = self._load_model(self.model_name)
        self._faiss = self._load_faiss()

        self.index = None
        self.remarks: list[str] = []

    @staticmethod
    def _load_numpy():
        try:
            import numpy as np
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Missing dependency: numpy. Install with `pip install numpy`."
            ) from exc
        return np

    @staticmethod
    def _load_model(model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Missing dependency: sentence-transformers. Install with `pip install sentence-transformers`."
            ) from exc

        return SentenceTransformer(model_name)

    @staticmethod
    def _load_faiss():
        try:
            import faiss
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Missing dependency: faiss-cpu. Install with `pip install faiss-cpu`."
            ) from exc

        return faiss

    def _encode(self, texts: list[str]) -> Any:
        np = self._load_numpy()
        emb = self._model.encode(texts, convert_to_numpy=True)
        emb = np.asarray(emb, dtype=np.float32)
        if emb.ndim != 2:
            raise ValueError("Embedding output must be 2D [n, dim].")
        if emb.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Embedding dim mismatch: expected {self.embedding_dim}, got {emb.shape[1]}"
            )
        return emb

    def build_index(self, remarks: Iterable[str]) -> None:
        clean_remarks = [r.strip() for r in remarks if isinstance(r, str) and r.strip()]
        if not clean_remarks:
            raise ValueError("No valid remarks provided to build index.")

        embeddings = self._encode(clean_remarks)
        self._faiss.normalize_L2(embeddings)

        index = self._faiss.IndexFlatIP(self.embedding_dim)
        index.add(embeddings)

        self.index = index
        self.remarks = clean_remarks

    def embed_query(self, query: str) -> Any:
        if not query or not query.strip():
            raise ValueError("query cannot be empty.")
        query_emb = self._encode([query.strip()])
        self._faiss.normalize_L2(query_emb)
        return query_emb

    def search_by_embedding(self, query_embedding: Any, top_k: int = 10) -> list[SearchHit]:
        if self.index is None:
            raise RuntimeError("Index not built yet. Call build_index() first.")

        k = max(1, min(int(top_k), len(self.remarks)))

        np = self._load_numpy()
        query_emb = np.asarray(query_embedding, dtype=np.float32)
        if query_emb.ndim != 2 or query_emb.shape[0] != 1 or query_emb.shape[1] != self.embedding_dim:
            raise ValueError(
                f"query_embedding must have shape (1, {self.embedding_dim}), got {tuple(query_emb.shape)}"
            )
        scores, indices = self.index.search(query_emb, k)

        results: list[SearchHit] = []
        for rank, idx in enumerate(indices[0]):
            if idx < 0:
                continue
            results.append(
                SearchHit(index=int(idx), remark=self.remarks[idx], score=float(scores[0][rank]))
            )
        return results

    def search_with_indices(self, query: str, top_k: int = 10) -> list[SearchHit]:
        query_emb = self.embed_query(query)
        return self.search_by_embedding(query_emb, top_k=top_k)

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        hits = self.search_with_indices(query=query, top_k=top_k)
        return [SearchResult(remark=h.remark, score=h.score) for h in hits]


def load_remarks_from_csv(csv_path: str | Path, text_col: str = "remarks") -> list[str]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    rows: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or text_col not in reader.fieldnames:
            raise ValueError(f"Column '{text_col}' not found in CSV. Available: {reader.fieldnames}")
        for row in reader:
            val = row.get(text_col)
            if val and val.strip():
                rows.append(val.strip())
    return rows
