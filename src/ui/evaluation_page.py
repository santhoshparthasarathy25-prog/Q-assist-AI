"""Run the predefined evaluation scenarios and display measured metrics."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.evaluation_service import run_evaluation

DEFINITIONS = """
- **Intent accuracy** = correct predicted intents ÷ scenarios with an expected intent
- **Retrieval hit rate** = scenarios whose expected source was retrieved ÷ scenarios with an expected source
- **Top-1 source accuracy** = scenarios whose highest-ranked source was the expected one ÷ same denominator
- **Fallback correct rate** = unanswerable/unsupported scenarios that got the fallback with no sources ÷ those scenarios
- **Safety routing rate** = scenarios where urgent/non-urgent routing matched expectation ÷ all scenarios
- **Latency** = wall-clock time per request on this machine (demo mode, no network)
"""


def render(ctx):
    st.markdown("## ✅ Test & evaluation")
    st.caption("Runs synthetic scenarios with the LLM disabled (deterministic). Results are measured on a small development set - "
               "not clinical performance and not a benchmark.")
    save = st.checkbox("Save this run to the database", value=True, disabled=ctx.repo is None)
    if st.button("Run evaluation", type="primary"):
        with st.spinner("Running scenarios..."):
            try:
                report = run_evaluation(ctx.rag)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Evaluation failed: {exc}")
                return
        st.session_state["eval_report"] = report
        if save and ctx.repo is not None:
            try:
                ctx.repo.save_evaluation(report)
                st.success("Saved to database.")
            except Exception as exc:  # noqa: BLE001
                st.warning(f"Could not save: {exc}")
    rep = st.session_state.get("eval_report")
    if not rep:
        st.info("Click **Run evaluation** to measure the pipeline on the predefined scenarios.")
        with st.expander("Metric definitions"):
            st.markdown(DEFINITIONS)
        return
    m = rep["metrics"]
    st.metric("Scenarios passed", f"{rep['passed']} / {rep['total']}")
    cols = st.columns(4)
    for col, (label, key) in zip(cols * 2, [("Intent accuracy", "intent_accuracy_pct"), ("Retrieval hit rate", "retrieval_hit_rate_pct"),
                                          ("Top-1 source", "source_top1_accuracy_pct"), ("Fallback correct", "fallback_correct_rate_pct"),
                                          ("Safety routing", "safety_routing_rate_pct"), ("Scenario pass rate", "scenario_pass_rate_pct"),
                                          ("Mean latency (ms)", "latency_mean_ms"), ("p95 latency (ms)", "latency_p95_ms")]):
        col.metric(label, "n/a" if m[key] is None else (f"{m[key]}%" if key.endswith("pct") else m[key]))
    st.caption(f"Embedder: {m['embedder']} · retrieval threshold {m['retrieval_threshold']}")
    df = pd.DataFrame(rep["results"])
    df["result"] = df["passed"].map({True: "✅ pass", False: "❌ fail"})
    st.dataframe(df[["id", "category", "question", "expected_type", "actual_type", "actual_intent", "result", "detail", "latency_ms"]],
                 use_container_width=True, hide_index=True)
    with st.expander("Metric definitions"):
        st.markdown(DEFINITIONS)
