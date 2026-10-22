"""Receptionist dashboard - every figure is computed from the local SQLite database."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from src.database.init_db import reset_db, seed_demo_data
from src.nlp.intent_classifier import INTENTS


def _bar(df, index, caption):
    if df.empty:
        st.caption("No data for the selected filters.")
    else:
        st.caption(caption)
        st.bar_chart(df.set_index(index), color="#13A89E")


def render(ctx):
    st.markdown("## 📊 Receptionist dashboard")
    st.caption("All numbers below are calculated from demo conversations stored in the local database (synthetic data only).")
    if ctx.repo is None:
        st.error(ctx.db_error or "Database unavailable.")
        return

    with st.expander("Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        today = dt.date.today()
        rng = c1.date_input("Date range", value=(today - dt.timedelta(days=30), today))
        intent = c2.selectbox("Intent", ["all"] + INTENTS)
        mode = c3.selectbox("Answer source", ["all", "live", "demo", "rule"],
                            help="live = LLM; demo = extracted from documents; rule = fixed safety/fallback text")
    d_from, d_to = (rng[0], rng[1]) if isinstance(rng, tuple) and len(rng) == 2 else (None, None)
    f = dict(date_from=d_from, date_to=d_to, intent=intent, mode=mode)

    try:
        k = ctx.repo.kpis(**f)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not read dashboard data: {exc}")
        return
    if k["enquiries"] == 0:
        st.info("No demo interactions match yet. Chat on the Chat page, or load the synthetic sample data below.")
    a, b, c = st.columns(3)
    a.metric("Demo conversations", k["conversations"])
    b.metric("User enquiries", k["enquiries"])
    c.metric("Escalations (simulated)", k["escalations"])

    l, r = st.columns(2)
    with l:
        st.markdown("**Intent distribution**")
        _bar(ctx.repo.intent_distribution(**f), "intent", "Enquiries by detected intent")
    with r:
        st.markdown("**Request status distribution**")
        _bar(ctx.repo.status_distribution(**f), "status", "Simulated workflow statuses")
    l, r = st.columns(2)
    with l:
        st.markdown("**LLM vs demo-mode usage**")
        _bar(ctx.repo.mode_usage(**f), "mode", "live = LLM answer · demo = extracted text · rule = fixed text")
    with r:
        st.markdown("**Source retrieval statistics**")
        ss = ctx.repo.source_stats(**f)
        st.write(f"Enquiries with ≥1 cited source: **{ss['with_sources']}** of **{ss['total']}**")
        if not ss["per_source"].empty:
            st.dataframe(ss["per_source"], use_container_width=True, hide_index=True)
    st.markdown("**Recent interactions**")
    recent = ctx.repo.recent_interactions(15, **f)
    st.dataframe(recent, use_container_width=True, hide_index=True) if not recent.empty else st.caption("Nothing to show.")

    st.markdown("**Latest saved evaluation (labelled evaluation data)**")
    ev = ctx.repo.latest_evaluation()
    if ev:
        m = ev["metrics"]
        st.write(f"Run at {ev['started_at']}: {ev['passed']}/{ev['total']} scenarios passed · "
                 f"intent accuracy {m.get('intent_accuracy_pct')}% · retrieval hit rate {m.get('retrieval_hit_rate_pct')}%")
    else:
        st.caption("No saved evaluation run yet - run one on the Evaluation page and tick 'save'.")

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("Load synthetic sample data", help="Replays data/seed/sample_data.json through the pipeline (uses your current mode; live mode makes a few API calls)"):
        with st.spinner("Seeding..."):
            n = seed_demo_data(ctx.service, ctx.convs, ctx.settings.seed_file)
        st.success(f"Processed {n} synthetic questions.")
        st.rerun()
    with c2:
        confirm = st.checkbox("I understand this deletes all demo conversations and saved evaluations")
        if st.button("Reset demo data", disabled=not confirm):
            reset_db(ctx.settings.db_path)
            st.session_state.pop("conversation_id", None)
            st.session_state.messages = []
            st.success("Demo data reset.")
            st.rerun()
