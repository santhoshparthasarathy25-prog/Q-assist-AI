"""Orchestrates one user turn.

Order of operations (safety first):
 1. validate input
 2. deterministic urgent check (no LLM)            -> escalate
 3. prompt-injection check on user text            -> decline
 4. intent classification
 5. human request / unsupported medical advice     -> fixed responses (no LLM)
 6. RAG retrieval + relevance threshold            -> fallback if weak (no LLM)
 7. LLM answer (live) or deterministic demo answer (honestly labelled)
 8. simulated workflow routing
 9. optional persistence"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from config.settings import Settings, get_settings
from src.llm.demo_responder import demo_answer
from src.llm.llm_service import LLMService
from src.llm.prompt_builder import build_prompts
from src.nlp.intent_classifier import IntentResult, classify_intent
from src.rag.rag_pipeline import RagPipeline
from src.safety import escalation as esc
from src.safety.safety_rules import check_urgent, looks_like_injection
from src.workflows.request_router import WorkflowOutcome, route_request

log = logging.getLogger(__name__)


@dataclass
class ReceptionistResponse:
    answer: str
    response_type: str  # answer | urgent | handoff | unsupported | fallback | invalid | injection
    answer_mode: str  # live | demo | rule  (rule = fixed safety/fallback text, no LLM involved)
    intent: IntentResult
    workflow: WorkflowOutcome
    escalation: esc.EscalationDecision
    sources: List[Dict] = field(default_factory=list)
    retrieval_note: str = ""
    best_score: float = 0.0
    latency_ms: float = 0.0
    llm_error: Optional[str] = None
    llm_error_kind: Optional[str] = None
    persist_error: Optional[str] = None
    message_id: Optional[int] = None


class ReceptionistService:
    def __init__(self, rag: RagPipeline, llm: LLMService, settings: Settings | None = None, repo=None):
        self.rag, self.llm, self.s, self.repo = rag, llm, settings or get_settings(), repo

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def _is_follow_up(question: str) -> bool:
        """A follow-up depends on earlier context: starts with a connective or uses a pronoun."""
        q = question.lower().strip()
        words = set(q.replace("?", " ").replace(",", " ").split())
        starts = q.startswith(("and ", "what about", "how about", "also ", "so "))
        return starts or bool(words & {"it", "that", "this", "those", "them", "there", "one"})

    def _finish(self, t0, **kw) -> ReceptionistResponse:
        kw["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        return ReceptionistResponse(**kw)

    # -- main entry --------------------------------------------------------
    def handle(self, question: str, history: Sequence[Tuple[str, str]] = (), conversation_id: Optional[int] = None,
               persist: bool = True) -> ReceptionistResponse:
        t0 = time.perf_counter()
        question = (question or "").strip()
        no_esc = esc.EscalationDecision(False)

        if not question or len(question) > self.s.max_input_chars:
            intent = classify_intent("")
            resp = self._finish(t0, answer=esc.INVALID_INPUT_MESSAGE.format(limit=self.s.max_input_chars),
                                response_type="invalid", answer_mode="rule", intent=intent,
                                workflow=route_request(intent, False), escalation=no_esc)
            return resp  # invalid input is not persisted

        # 2. urgent check FIRST
        urgent = check_urgent(question)
        if urgent.is_urgent:
            intent = classify_intent(question)
            resp = self._finish(t0, answer=esc.URGENT_MESSAGE, response_type="urgent", answer_mode="rule",
                                intent=intent, workflow=route_request(intent), escalation=esc.urgent_decision(urgent.category))
            return self._persist(resp, question, conversation_id, persist)

        # 3. injection attempts in user text
        if looks_like_injection(question):
            intent = classify_intent("")
            intent.reason = "Prompt-injection pattern detected in user text"
            resp = self._finish(t0, answer=esc.INJECTION_MESSAGE, response_type="injection", answer_mode="rule",
                                intent=intent, workflow=route_request(intent, False), escalation=no_esc)
            return self._persist(resp, question, conversation_id, persist)

        # 4. intent on the question alone
        last_user = next((txt for r, txt in reversed(list(history)) if r == "user"), "")
        intent = classify_intent(question)

        # 5. fixed-response intents
        if intent.label == "human_assistance":
            resp = self._finish(t0, answer=esc.HUMAN_HANDOFF_MESSAGE, response_type="handoff", answer_mode="rule",
                                intent=intent, workflow=route_request(intent), escalation=esc.human_decision())
            return self._persist(resp, question, conversation_id, persist)
        if intent.label == "unsupported":
            resp = self._finish(t0, answer=esc.UNSUPPORTED_MEDICAL_MESSAGE, response_type="unsupported",
                                answer_mode="rule", intent=intent, workflow=route_request(intent), escalation=no_esc)
            return self._persist(resp, question, conversation_id, persist)

        # 6. retrieval on the question alone; only a genuine follow-up may borrow the previous user message
        ret = self.rag.retrieve(question)
        if last_user and (not ret.reliable or intent.label == "unknown") and self._is_follow_up(question):
            combined_q = f"{last_user} {question}"
            ret2 = self.rag.retrieve(combined_q)
            if ret2.reliable:
                ret = ret2
                if intent.label == "unknown":
                    c_intent = classify_intent(combined_q)
                    if c_intent.label not in ("urgent", "unsupported", "human_assistance"):
                        intent = c_intent
                        intent.reason += " (using previous message as context)"
        sources = [{"chunk_id": h.chunk_id, "source": h.source, "score": round(h.score, 4), "text": h.text}
                   for h in ret.hits]
        if not ret.reliable:
            resp = self._finish(t0, answer=esc.NO_VERIFIED_INFO_MESSAGE, response_type="fallback", answer_mode="rule",
                                intent=intent, workflow=route_request(intent, False), escalation=no_esc,
                                retrieval_note=ret.note, best_score=ret.best_score)
            return self._persist(resp, question, conversation_id, persist)

        # 7. LLM or demo
        system, user = build_prompts(question, ret.hits, history, self.s.history_turns)
        llm_res = self.llm.generate(system, user)
        if llm_res.mode == "live":
            answer, mode = llm_res.text, "live"
        else:
            answer, mode = demo_answer(question, ret.hits), "demo"

        resp = self._finish(t0, answer=answer, response_type="answer", answer_mode=mode, intent=intent,
                            workflow=route_request(intent, True), escalation=no_esc, sources=sources,
                            retrieval_note=ret.note, best_score=ret.best_score,
                            llm_error=llm_res.error, llm_error_kind=llm_res.error_kind)
        return self._persist(resp, question, conversation_id, persist)

    def _persist(self, resp: ReceptionistResponse, question: str, conversation_id, persist: bool):
        if persist and self.repo is not None and conversation_id is not None:
            try:
                resp.message_id = self.repo.record_interaction(conversation_id, question, resp)
            except Exception as exc:  # noqa: BLE001 - the chat must keep working if the DB fails
                log.error("Could not save interaction: %s", type(exc).__name__)
                resp.persist_error = "Could not save this interaction to the local database."
        return resp
