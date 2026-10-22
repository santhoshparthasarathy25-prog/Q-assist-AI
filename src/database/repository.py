"""All database reads/writes live here so the rest of the app never writes SQL directly."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd
from sqlalchemy import select, text

from src.database.connection import make_session_factory, session_scope
from src.database.models import (AdminRequest, Conversation, EscalationEvent, EvaluationResult, EvaluationRun,
                                 IntentRecord, Message, SourceRecord)
from src.utils.exceptions import DatabaseError
from src.utils.privacy import redact

URGENT_PLACEHOLDER = "[urgent message - content not stored]"


class Repository:
    def __init__(self, engine):
        self.engine = engine
        self.factory = make_session_factory(engine)

    # ---- conversations ---------------------------------------------------
    def create_conversation(self, session_id: str, is_seed: bool = False) -> int:
        with session_scope(self.factory) as s:
            c = Conversation(session_id=session_id, is_seed=is_seed)
            s.add(c)
            s.flush()
            return c.id

    def end_conversation(self, conversation_id: int) -> None:
        with session_scope(self.factory) as s:
            c = s.get(Conversation, conversation_id)
            if c and c.ended_at is None:
                c.ended_at = datetime.utcnow()

    def get_history(self, conversation_id: int, limit: int = 12) -> List[Tuple[str, str]]:
        """History for ONE conversation id only (session isolation)."""
        with session_scope(self.factory) as s:
            rows = s.execute(select(Message.role, Message.content).where(Message.conversation_id == conversation_id)
                             .order_by(Message.id.desc()).limit(limit)).all()
        return [(r, c) for r, c in reversed(rows)]

    # ---- recording -------------------------------------------------------
    def record_interaction(self, conversation_id: int, question: str, resp) -> int:
        """Store the user message, assistant message, intent, sources, workflow request and escalation."""
        stored_q = URGENT_PLACEHOLDER if resp.response_type == "urgent" else redact(question)
        with session_scope(self.factory) as s:
            user_msg = Message(conversation_id=conversation_id, role="user", content=stored_q)
            s.add(user_msg)
            s.flush()
            s.add(Message(conversation_id=conversation_id, role="assistant", content=resp.answer))
            i = resp.intent
            s.add(IntentRecord(message_id=user_msg.id, label=i.label, rule_matches=i.rule_matches, reason=i.reason[:255],
                               workflow=i.workflow, escalation_required=resp.escalation.required,
                               answer_mode=resp.answer_mode, response_type=resp.response_type,
                               latency_ms=resp.latency_ms))
            for rank, src in enumerate(resp.sources, 1):
                s.add(SourceRecord(message_id=user_msg.id, source=src["source"], chunk_id=src["chunk_id"],
                                   score=src["score"], rank=rank))
            w = resp.workflow
            if w.request_type:
                s.add(AdminRequest(message_id=user_msg.id, request_type=w.request_type, status=w.status,
                                   simulated=w.simulated, description=w.description[:300]))
            if resp.escalation.required:
                s.add(EscalationEvent(message_id=user_msg.id, kind=resp.escalation.kind or "unknown",
                                      reason=(resp.escalation.reason or "")[:100]))
            return user_msg.id

    # ---- dashboard queries (example SQL is documented in docs/database_schema.md) ----
    def _df(self, sql: str, params: Optional[dict] = None) -> pd.DataFrame:
        try:
            with self.engine.connect() as conn:
                return pd.read_sql_query(text(sql), conn, params=params or {})
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(f"Query failed: {type(exc).__name__}") from exc

    @staticmethod
    def _filters(date_from, date_to, intent, mode, alias="i") -> Tuple[str, dict]:
        clauses, p = ["1=1"], {}
        if date_from:
            clauses.append(f"date({alias}.created_at) >= :d1"); p["d1"] = str(date_from)
        if date_to:
            clauses.append(f"date({alias}.created_at) <= :d2"); p["d2"] = str(date_to)
        if intent and intent != "all":
            clauses.append(f"{alias}.label = :intent" if alias == "i" else "i.label = :intent"); p["intent"] = intent
        if mode and mode != "all":
            clauses.append("i.answer_mode = :mode"); p["mode"] = mode
        return " AND ".join(clauses), p

    def kpis(self, **f) -> Dict[str, int]:
        where, p = self._filters(f.get("date_from"), f.get("date_to"), f.get("intent"), f.get("mode"))
        d = self._df(f"""SELECT COUNT(DISTINCT m.conversation_id) AS conversations, COUNT(*) AS enquiries,
                         COALESCE(SUM(i.escalation_required),0) AS escalations
                         FROM intent_records i JOIN messages m ON m.id=i.message_id WHERE {where}""", p)
        return {k: int(d.iloc[0][k]) for k in d.columns}

    def intent_distribution(self, **f) -> pd.DataFrame:
        where, p = self._filters(f.get("date_from"), f.get("date_to"), f.get("intent"), f.get("mode"))
        return self._df(f"SELECT i.label AS intent, COUNT(*) AS count FROM intent_records i WHERE {where} "
                        "GROUP BY i.label ORDER BY count DESC", p)

    def status_distribution(self, **f) -> pd.DataFrame:
        where, p = self._filters(f.get("date_from"), f.get("date_to"), f.get("intent"), f.get("mode"))
        return self._df(f"""SELECT r.status AS status, COUNT(*) AS count FROM admin_requests r
                            JOIN intent_records i ON i.message_id=r.message_id WHERE {where}
                            GROUP BY r.status ORDER BY count DESC""", p)

    def mode_usage(self, **f) -> pd.DataFrame:
        where, p = self._filters(f.get("date_from"), f.get("date_to"), f.get("intent"), f.get("mode"))
        return self._df(f"SELECT i.answer_mode AS mode, COUNT(*) AS count FROM intent_records i WHERE {where} "
                        "GROUP BY i.answer_mode", p)

    def source_stats(self, **f) -> Dict[str, object]:
        where, p = self._filters(f.get("date_from"), f.get("date_to"), f.get("intent"), f.get("mode"))
        d = self._df(f"""SELECT COUNT(*) AS total,
                         SUM(CASE WHEN EXISTS (SELECT 1 FROM source_records s WHERE s.message_id=i.message_id) THEN 1 ELSE 0 END) AS with_sources
                         FROM intent_records i WHERE {where}""", p)
        per = self._df(f"""SELECT s.source AS source, COUNT(*) AS retrievals, ROUND(AVG(s.score),3) AS avg_score
                           FROM source_records s JOIN intent_records i ON i.message_id=s.message_id
                           WHERE {where} GROUP BY s.source ORDER BY retrievals DESC""", p)
        total = int(d.iloc[0]["total"] or 0)
        withs = int(d.iloc[0]["with_sources"] or 0)
        return {"total": total, "with_sources": withs, "without_sources": total - withs, "per_source": per}

    def recent_interactions(self, limit: int = 15, **f) -> pd.DataFrame:
        where, p = self._filters(f.get("date_from"), f.get("date_to"), f.get("intent"), f.get("mode"))
        p["limit"] = limit
        return self._df(f"""SELECT i.created_at AS time, m.content AS enquiry, i.label AS intent, i.answer_mode AS mode,
                            i.response_type AS outcome,
                            (SELECT r.status FROM admin_requests r WHERE r.message_id=i.message_id) AS status,
                            i.escalation_required AS escalated
                            FROM intent_records i JOIN messages m ON m.id=i.message_id WHERE {where}
                            ORDER BY i.id DESC LIMIT :limit""", p)

    # ---- evaluation ------------------------------------------------------
    def save_evaluation(self, report: Dict) -> int:
        with session_scope(self.factory) as s:
            run = EvaluationRun(total=report["total"], passed=report["passed"], metrics_json=json.dumps(report["metrics"]))
            s.add(run)
            s.flush()
            for r in report["results"]:
                s.add(EvaluationResult(run_id=run.id, scenario_id=r["id"], category=r["category"], passed=r["passed"],
                                       expected_intent=r.get("expected_intent"), actual_intent=r.get("actual_intent"),
                                       latency_ms=r["latency_ms"], detail=r.get("detail", "")[:300]))
            return run.id

    def latest_evaluation(self) -> Optional[Dict]:
        runs = self._df("SELECT id, started_at, total, passed, metrics_json FROM evaluation_runs ORDER BY id DESC LIMIT 1")
        if runs.empty:
            return None
        row = runs.iloc[0]
        res = self._df("SELECT scenario_id AS id, category, passed, expected_intent, actual_intent, latency_ms, detail "
                       "FROM evaluation_results WHERE run_id=:r", {"r": int(row["id"])})
        return {"started_at": row["started_at"], "total": int(row["total"]), "passed": int(row["passed"]),
                "metrics": json.loads(row["metrics_json"]), "results": res}
