"""Configuration and system status. Never displays secret values."""
from __future__ import annotations

import importlib.util
import platform
import sys

import streamlit as st

from config.settings import PROMPT_VERSION


def _has(mod: str) -> str:
    try:
        return "installed" if importlib.util.find_spec(mod) else "not installed"
    except (ImportError, ValueError):
        return "not installed"


def render(ctx):
    s = ctx.settings
    st.markdown("## ⚙️ Configuration & system status")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### LLM")
        if ctx.llm.available:
            st.success("API key detected - live mode possible")
        else:
            st.warning("No API key - running in **demo mode** (answers are extracted from documents, not LLM generated)")
        st.write({"model": s.gemini_model, "timeout_seconds": s.llm_timeout_seconds, "api_key_set": s.llm_configured,
                  "prompt_version": PROMPT_VERSION})
        if st.button("Test LLM connection"):
            with st.spinner("Calling model..."):
                r = ctx.llm.generate("Reply with the single word OK.", "ping")
            (st.success(f"Live response received: {r.text[:60]}") if r.mode == "live" else st.error(r.error))
        st.markdown("#### Retrieval")
        stt = ctx.rag.status()
        st.write({"embedder": stt["embedder"], "note": stt["note"], "documents": stt["documents"], "chunks": stt["chunks"],
                  "top_k": s.retrieval_top_k,
                  "threshold": ctx.rag.retriever.threshold if ctx.rag.retriever else None})
    with c2:
        st.markdown("#### Storage")
        size = s.db_path.stat().st_size / 1024 if s.db_path.exists() else 0
        st.write({"database_file": str(s.db_path), "database_size_kb": round(size, 1), "database_ok": ctx.repo is not None,
                  "index_folder": str(ctx.rag.index_dir)})
        if ctx.db_error:
            st.warning(ctx.db_error)
        st.markdown("#### Environment")
        st.write({"python": sys.version.split()[0], "platform": platform.platform(),
                  "streamlit": _has("streamlit"), "sentence_transformers": _has("sentence_transformers"),
                  "google_genai": _has("google.genai"), "pypdf": _has("pypdf"), "pyttsx3 (optional)": _has("pyttsx3")})
    st.info("Settings are read from environment variables / `.env` at startup. Restart the app after changing them.")
