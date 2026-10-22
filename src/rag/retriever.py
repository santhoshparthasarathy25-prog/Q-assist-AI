"""Retrieve chunks and apply an explicit relevance threshold."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from src.rag.vector_store import SearchHit, VectorStore


@dataclass
class RetrievalResult:
    hits: List[SearchHit] = field(default_factory=list)  # chunks above the threshold only
    best_score: float = 0.0
    threshold: float = 0.0
    reliable: bool = False
    note: str = ""


class Retriever:
    def __init__(self, embedder, store: VectorStore, threshold: float, top_k: int = 3):
        self.embedder, self.store, self.threshold, self.top_k = embedder, store, threshold, top_k

    def retrieve(self, query: str) -> RetrievalResult:
        if not query.strip() or len(self.store) == 0:
            return RetrievalResult(threshold=self.threshold, note="Empty query or empty index")
        qv = self.embedder.encode([query])[0]
        raw = self.store.search(qv, self.top_k)
        best = raw[0].score if raw else 0.0
        kept = [h for h in raw if h.score >= self.threshold]
        note = "Relevant context found" if kept else "Best match below relevance threshold - treated as not found"
        return RetrievalResult(kept, best, self.threshold, bool(kept), note)
