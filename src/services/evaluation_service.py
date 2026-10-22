"""Reproducible evaluation over data/evaluation/evaluation_questions.json.

Everything runs WITHOUT a live API: the LLM is disabled (demo mode) or replaced by a failing stub.
Metric definitions (also in docs/testing_report.md):
- intent_accuracy        = scenarios whose predicted intent == expected_intent / scenarios with an expected_intent
- retrieval_hit_rate     = scenarios where expected_source is among the retrieved (above-threshold) sources / scenarios with expected_source
- source_top1_accuracy   = scenarios where the highest-ranked source == expected_source / scenarios with expected_source
- fallback_correct_rate  = scenarios expecting fallback/unsupported that returned that response type with NO sources / scenarios expecting it
- safety_routing_rate    = scenarios where (response_type == 'urgent') matches (expected response_type == 'urgent') / all scenarios
- scenario_pass_rate     = scenarios meeting every expectation / all scenarios
- latency                = wall-clock ms per handle() call (retrieval + rules + demo answer), this machine only"""
from __future__ import annotations

import dataclasses
import json
import statistics
from pathlib import Path
from typing import Dict

from config.settings import get_settings
from src.llm.llm_service import LLMService
from src.services.receptionist_service import ReceptionistService


class _FailingClient:
    """Stub that simulates a network failure inside the LLM client."""
    class models:
        @staticmethod
        def generate_content(**_):
            raise ConnectionError("simulated network failure")


def _pct(n: int, d: int):
    return None if d == 0 else round(100.0 * n / d, 1)


def run_evaluation(rag, eval_file: Path | None = None) -> Dict:
    s = get_settings()
    s_nokey = dataclasses.replace(s, gemini_api_key="")
    scenarios = json.loads(Path(eval_file or s.eval_file).read_text(encoding="utf-8"))["scenarios"]
    base = ReceptionistService(rag, LLMService(s_nokey), s_nokey)
    failing = ReceptionistService(rag, LLMService(s_nokey, client=_FailingClient()), s_nokey)

    results, lat = [], []
    c = dict(ia_n=0, ia_ok=0, rh_n=0, rh_ok=0, t1_ok=0, fb_n=0, fb_ok=0, sf_ok=0)
    for sc in scenarios:
        svc = failing if sc.get("llm") == "fail" else base
        hist = [tuple(h) for h in sc.get("history", [])]
        question = sc["question"] if "question_gen" not in sc else sc["question_gen"]["char"] * sc["question_gen"]["n"]
        r = svc.handle(question, hist, persist=False)
        lat.append(r.latency_ms)
        problems = []
        exp_i, exp_t = sc.get("expected_intent"), sc["expected_response_type"]
        if exp_i and r.intent.label != exp_i:
            problems.append(f"intent {r.intent.label}!={exp_i}")
        if r.response_type != exp_t:
            problems.append(f"type {r.response_type}!={exp_t}")
        if r.escalation.required != sc.get("expect_escalation", False):
            problems.append("escalation mismatch")
        if sc.get("llm") == "fail" and r.llm_error_kind != "network":
            problems.append("llm failure not surfaced as network error")
        if sc.get("llm") == "fail" and r.answer_mode == "live":
            problems.append("fallback wrongly shown as live")
        src_names = [x["source"] for x in r.sources]
        exp_s = sc.get("expected_source")
        if exp_i:
            c["ia_n"] += 1; c["ia_ok"] += r.intent.label == exp_i
        if exp_s:
            c["rh_n"] += 1; c["rh_ok"] += exp_s in src_names; c["t1_ok"] += bool(src_names) and src_names[0] == exp_s
            if exp_s not in src_names:
                problems.append(f"source {exp_s} not retrieved")
        if exp_t in ("fallback", "unsupported"):
            c["fb_n"] += 1; ok = r.response_type == exp_t and not r.sources; c["fb_ok"] += ok
            if r.sources:
                problems.append("fabricated/unexpected sources")
        c["sf_ok"] += (r.response_type == "urgent") == (exp_t == "urgent")
        results.append({"id": sc["id"], "category": sc["category"], "question": question[:80],
                        "passed": not problems, "expected_intent": exp_i, "actual_intent": r.intent.label,
                        "expected_type": exp_t, "actual_type": r.response_type, "mode": r.answer_mode,
                        "best_score": round(r.best_score, 3), "latency_ms": r.latency_ms, "detail": "; ".join(problems)})

    n = len(results)
    passed = sum(x["passed"] for x in results)
    metrics = {
        "intent_accuracy_pct": _pct(c["ia_ok"], c["ia_n"]),
        "retrieval_hit_rate_pct": _pct(c["rh_ok"], c["rh_n"]),
        "source_top1_accuracy_pct": _pct(c["t1_ok"], c["rh_n"]),
        "fallback_correct_rate_pct": _pct(c["fb_ok"], c["fb_n"]),
        "safety_routing_rate_pct": _pct(c["sf_ok"], n),
        "scenario_pass_rate_pct": _pct(passed, n),
        "latency_mean_ms": round(statistics.mean(lat), 2) if lat else None,
        "latency_p95_ms": round(sorted(lat)[max(0, int(0.95 * len(lat)) - 1)], 2) if lat else None,
        "embedder": rag.embedder.name, "retrieval_threshold": rag.retriever.threshold if rag.retriever else None,
        "counts": c,
    }
    return {"total": n, "passed": passed, "metrics": metrics, "results": results}
