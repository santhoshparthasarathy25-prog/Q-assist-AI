"""RAG pipeline: load -> clean -> chunk -> embed -> persist -> retrieve -> threshold."""
from __future__ import annotations

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict

from config.settings import Settings, get_settings
from src.rag.chunker import chunk_documents
from src.rag.document_loader import load_documents
from src.rag.embeddings import create_embedder
from src.rag.retriever import RetrievalResult, Retriever
from src.rag.vector_store import VectorStore

log = logging.getLogger(__name__)


class RagPipeline:
    def __init__(self, settings: Settings | None = None, kb_dir: Path | None = None, storage_dir: Path | None = None):
        self.s = settings or get_settings()
        self.kb_dir = Path(kb_dir or self.s.kb_dir)
        self.index_dir = Path(storage_dir or self.s.storage_dir) / "index"
        self.manifest_path = self.index_dir / "manifest.json"
        self.store = VectorStore()
        self.embedder, self.backend_note = create_embedder(self.s.embedding_backend, self.s.embedding_model)
        self.warnings: list[str] = []
        self.retriever: Retriever | None = None
        self.ready = False

    # ---- indexing -------------------------------------------------------
    def _fingerprint(self, docs) -> Dict:
        return {"embedder": self.embedder.name, "files": {d.source: d.sha256 for d in docs}}

    def ingest(self, force: bool = False) -> Dict:
        """Index the knowledge base. Skips work when files and embedder are unchanged."""
        docs, self.warnings = load_documents(self.kb_dir)
        fp = self._fingerprint(docs)
        if not force and self.manifest_path.exists():
            try:
                old = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                if old == fp and self.store.load(self.index_dir) and self.embedder.load(self.index_dir):
                    self._make_retriever()
                    return {"status": "up_to_date", "documents": len(docs), "chunks": len(self.store)}
            except (OSError, ValueError):
                log.warning("Manifest unreadable; rebuilding index")
        chunks = chunk_documents(docs)
        if not chunks:
            self.store.build(np.zeros((0, 0)), [])
            self.ready = False
            return {"status": "empty", "documents": len(docs), "chunks": 0}
        texts = [c.text for c in chunks]
        self.embedder.fit(texts)
        vectors = self.embedder.encode(texts)
        self.store.build(vectors, [{"chunk_id": c.chunk_id, "source": c.source, "text": c.text} for c in chunks])
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.store.save(self.index_dir)
        self.embedder.save(self.index_dir)
        self.manifest_path.write_text(json.dumps(fp), encoding="utf-8")
        self._make_retriever()
        return {"status": "rebuilt", "documents": len(docs), "chunks": len(chunks)}

    def _make_retriever(self) -> None:
        thr = self.s.threshold_dense if self.embedder.kind == "dense" else self.s.threshold_tfidf
        self.retriever = Retriever(self.embedder, self.store, thr, self.s.retrieval_top_k)
        self.ready = len(self.store) > 0

    # ---- querying -------------------------------------------------------
    def retrieve(self, query: str) -> RetrievalResult:
        if not self.ready or self.retriever is None:
            self.ingest()
        if self.retriever is None:
            return RetrievalResult(note="Knowledge base is empty")
        return self.retriever.retrieve(query)

    def status(self) -> Dict:
        return {"embedder": self.embedder.name, "note": self.backend_note, "chunks": len(self.store),
                "documents": len({m["source"] for m in self.store.meta}), "ready": self.ready,
                "warnings": self.warnings}
