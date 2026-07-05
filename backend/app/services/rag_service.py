"""Retrieval-Augmented Generation service using FAISS.

Chunks dataset rows, embeds them, stores in a FAISS index, and retrieves
relevant chunks for Gemini context.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("app.rag")

try:
    import faiss
    _FAISS_AVAILABLE = True
except ImportError:  # pragma: no cover
    faiss = None
    _FAISS_AVAILABLE = False


def _hash_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _simple_embed(text: str, dim: int = 256) -> np.ndarray:
    """Deterministic lightweight embedding when no embedding model is available.

    Uses character n-gram hashing into a fixed-size vector, then L2-normalizes.
    This is NOT a semantic embedding but provides a stable retrieval signal for
    the RAG pipeline without requiring an external embedding API.
    """
    vec = np.zeros(dim, dtype=np.float32)
    text = text.lower()
    for i in range(len(text)):
        vec[hash(text[i : i + 3]) % dim] += 1.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


class RAGIndex:
    """In-memory FAISS index for a single dataset."""

    def __init__(self, dataset_id: str, dim: int = 256):
        self.dataset_id = dataset_id
        self.dim = dim
        self.chunks: List[str] = []
        self.metadata: List[dict] = []
        self.index = None
        if _FAISS_AVAILABLE:
            self.index = faiss.IndexFlatIP(dim)

    def add_chunk(self, text: str, meta: Optional[dict] = None) -> None:
        if not text.strip():
            return
        self.chunks.append(text)
        self.metadata.append(meta or {})
        if self.index is not None:
            vec = _simple_embed(text, self.dim).reshape(1, -1)
            self.index.add(vec)

    def build_from_dataframe(self, df: pd.DataFrame, chunk_size: int = 5) -> None:
        """Chunk the dataframe into row-group text blocks."""
        for start in range(0, len(df), chunk_size):
            chunk_df = df.iloc[start : start + chunk_size]
            lines = []
            for _, row in chunk_df.iterrows():
                parts = [f"{c}={row[c]}" for c in df.columns if pd.notna(row[c])]
                lines.append(", ".join(parts))
            text = "\n".join(lines)
            self.add_chunk(text, {"rows": f"{start}-{start + len(chunk_df) - 1}"})
        logger.info("RAG index built for %s: %d chunks", self.dataset_id, len(self.chunks))

    def search(self, query: str, k: int = 5) -> List[Tuple[str, dict, float]]:
        if not self.chunks:
            return []
        if self.index is not None:
            vec = _simple_embed(query, self.dim).reshape(1, -1)
            k = min(k, self.index.ntotal)
            scores, indices = self.index.search(vec, k)
            return [
                (self.chunks[i], self.metadata[i], float(s))
                for s, i in zip(scores[0], indices[0])
                if i >= 0
            ]
        # Fallback: keyword overlap scoring
        scored = []
        q_lower = query.lower()
        for idx, chunk in enumerate(self.chunks):
            score = sum(1 for w in q_lower.split() if w in chunk.lower())
            scored.append((chunk, self.metadata[idx], score))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:k]


# In-process registry of RAG indexes keyed by dataset_id.
# For multi-instance deployments, persist embeddings to disk or a vector DB.
_registry: Dict[str, RAGIndex] = {}


def build_index(dataset_id: str, df: pd.DataFrame) -> RAGIndex:
    idx = RAGIndex(dataset_id)
    idx.build_from_dataframe(df)
    _registry[dataset_id] = idx
    return idx


def get_index(dataset_id: str) -> Optional[RAGIndex]:
    return _registry.get(dataset_id)


def retrieve_context(dataset_id: str, query: str, k: int = 5) -> List[str]:
    idx = get_index(dataset_id)
    if idx is None:
        return []
    results = idx.search(query, k=k)
    return [chunk for chunk, _, _ in results]
