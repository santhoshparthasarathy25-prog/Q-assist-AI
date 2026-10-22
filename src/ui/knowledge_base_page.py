"""Knowledge-base management: list, upload, re-index, and test retrieval."""
from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from src.rag.document_loader import SUPPORTED


def render(ctx):
    st.markdown("## 📚 Knowledge base")
    st.caption("Local documents the assistant may use. All bundled clinic details are **fictional**.")
    kb = ctx.settings.kb_dir
    files = sorted(p for p in kb.glob("*") if p.suffix.lower() in SUPPORTED)
    if files:
        st.dataframe(pd.DataFrame([{"file": p.name, "type": p.suffix.upper().strip("."), "size (KB)": round(p.stat().st_size / 1024, 1)}
                                   for p in files]), use_container_width=True, hide_index=True)
    else:
        st.info("No documents found. Upload a TXT or PDF file below.")

    st.markdown("#### Add a document")
    up = st.file_uploader("TXT or PDF", type=["txt", "pdf"], help="Do not upload real patient information.")
    if up is not None and st.button("Save and re-index"):
        name = re.sub(r"[^A-Za-z0-9._-]", "_", up.name)
        (kb / name).write_bytes(up.getvalue())
        with st.spinner("Indexing..."):
            st.session_state["kb_info"] = ctx.rag.ingest()
        st.success(f"Saved {name}.")
    c1, c2 = st.columns(2)
    if c1.button("Re-index (only if files changed)", help="Skips work when file contents are unchanged"):
        with st.spinner("Checking..."):
            st.session_state["kb_info"] = ctx.rag.ingest()
    if c2.button("Force full rebuild"):
        with st.spinner("Rebuilding..."):
            st.session_state["kb_info"] = ctx.rag.ingest(force=True)
    if "kb_info" in st.session_state:
        st.write(st.session_state["kb_info"])
    for w in ctx.rag.warnings:
        st.warning(w)
    stt = ctx.rag.status()
    st.caption(f"Embedder: {stt['embedder']} · {stt['note']} · {stt['documents']} documents · {stt['chunks']} chunks")

    st.markdown("#### Test retrieval")
    q = st.text_input("Search the knowledge base", placeholder="e.g. repeat prescription processing time")
    if q:
        res = ctx.rag.retrieve(q)
        st.write(f"Best score **{res.best_score:.3f}** vs threshold **{res.threshold}** - {res.note}")
        for h in res.hits:
            with st.expander(f"{h.source} · {h.chunk_id.split('::')[-1]} · {h.score:.3f}"):
                st.write(h.text)
    with st.expander("Browse indexed chunks"):
        if ctx.rag.store.meta:
            st.dataframe(pd.DataFrame(ctx.rag.store.meta)[["chunk_id", "text"]], use_container_width=True, hide_index=True)
