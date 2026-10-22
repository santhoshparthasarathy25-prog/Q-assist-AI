"""Small persistent vector store (exact cosine search with NumPy).

Why not FAISS/Chroma? For a knowledge base of a few hundred chunks, exact search in NumPy is
instant, has no native dependencies and is easy to explain. The interface (add/search/save/load)
is deliberately FAISS-like so it can be swapped later."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np


@dataclass
class SearchHit:
    chunk_id: str
    source: str
    text: str
    score: float


class VectorStore:
    def __init__(self):
        self.vectors = np.zeros((0, 0), dtype="float32")
        self.meta: List[Dict] = []

    def __len__(self) -> int:
        return len(self.meta)

    @staticmethod
    def _norm(m: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(m, axis=1, keepdims=True)
        n[n == 0] = 1.0
        return m / n

    def build(self, vectors: np.ndarray, meta: List[Dict]) -> None:
        self.vectors = self._norm(vectors.astype("float32")) if len(meta) else np.zeros((0, 0), "float32")
        self.meta = meta

    def search(self, query_vec: np.ndarray, k: int = 3) -> List[SearchHit]:
        if not self.meta:
            return []
        q = self._norm(query_vec.reshape(1, -1).astype("float32"))
        scores = (self.vectors @ q.T).ravel()
        order = np.argsort(-scores)[:k]
        return [SearchHit(self.meta[i]["chunk_id"], self.meta[i]["source"], self.meta[i]["text"], float(scores[i]))
                for i in order]

    def save(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        np.save(folder / "vectors.npy", self.vectors)
        (folder / "chunks.json").write_text(json.dumps(self.meta, ensure_ascii=False), encoding="utf-8")

    def load(self, folder: Path) -> bool:
        v, m = folder / "vectors.npy", folder / "chunks.json"
        if not (v.exists() and m.exists()):
            return False
        self.vectors = np.load(v)
        self.meta = json.loads(m.read_text(encoding="utf-8"))
        return True
