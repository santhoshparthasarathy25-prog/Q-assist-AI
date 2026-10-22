"""Embedding backends.

- SentenceTransformerEmbedder: dense semantic vectors (needs `sentence-transformers` and a one-off
  model download of roughly 90 MB for all-MiniLM-L6-v2).
- TfidfEmbedder: scikit-learn TF-IDF vectors. Lexical (keyword) matching only, no download.
  Used automatically when sentence-transformers is not installed or the model cannot be loaded.

Both expose the same tiny interface so the rest of the pipeline does not care which one is used."""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import List

import numpy as np

log = logging.getLogger(__name__)


# Generic request verbs carry no topic information and cause false keyword matches
# (e.g. "Do you OFFER physiotherapy?" matching "offer a new appointment").
GENERIC_QUERY_WORDS = {"offer", "offers", "offered", "provide", "provides", "provided", "give", "tell", "know",
                       "want", "need", "please", "help", "able", "get"}


class TfidfEmbedder:
    name = "tfidf"
    kind = "tfidf"

    def __init__(self):
        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
        stops = sorted(set(ENGLISH_STOP_WORDS) | GENERIC_QUERY_WORDS)
        self.vec = TfidfVectorizer(lowercase=True, stop_words=stops, ngram_range=(1, 2), sublinear_tf=True)
        self.fitted = False

    def fit(self, texts: List[str]) -> None:
        self.vec.fit(texts)
        self.fitted = True

    def encode(self, texts: List[str]) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("TfidfEmbedder must be fitted (index built) before use")
        return self.vec.transform(texts).toarray().astype("float32")

    def save(self, folder: Path) -> None:
        with open(folder / "tfidf_vectorizer.pkl", "wb") as f:
            pickle.dump(self.vec, f)

    def load(self, folder: Path) -> bool:
        p = folder / "tfidf_vectorizer.pkl"
        if not p.exists():
            return False
        with open(p, "rb") as f:  # local file written by this app only
            self.vec = pickle.load(f)
        self.fitted = True
        return True


class SentenceTransformerEmbedder:
    kind = "dense"

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # may raise ImportError / OSError
        self.model = SentenceTransformer(model_name)
        self.name = model_name

    def fit(self, texts: List[str]) -> None:  # nothing to fit
        return None

    def encode(self, texts: List[str]) -> np.ndarray:
        return np.asarray(self.model.encode(texts, normalize_embeddings=True), dtype="float32")

    def save(self, folder: Path) -> None:
        return None

    def load(self, folder: Path) -> bool:
        return True


def create_embedder(backend: str = "auto", model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Return (embedder, note). `note` explains any fallback so the UI can show it honestly."""
    backend = (backend or "auto").lower()
    if backend in ("auto", "sentence-transformers"):
        try:
            return SentenceTransformerEmbedder(model_name), "Using Sentence Transformers"
        except Exception as exc:  # noqa: BLE001
            note = f"Sentence Transformers unavailable ({type(exc).__name__}); using TF-IDF keyword fallback"
            log.warning(note)
            return TfidfEmbedder(), note
    return TfidfEmbedder(), "Using TF-IDF (configured)"
