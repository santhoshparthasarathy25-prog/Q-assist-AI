"""SQLAlchemy 2.0 ORM models. Synthetic/demo data only."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.utcnow()


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_seed: Mapped[bool] = mapped_column(Boolean, default=False)
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (CheckConstraint("role IN ('user','assistant')", name="ck_message_role"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class IntentRecord(Base):
    """Classification + processing outcome for one USER message."""
    __tablename__ = "intent_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), unique=True)
    label: Mapped[str] = mapped_column(String(32), index=True)
    rule_matches: Mapped[int] = mapped_column(Integer, default=0)  # count of matched rules, not a probability
    reason: Mapped[str] = mapped_column(String(255))
    workflow: Mapped[str] = mapped_column(String(48))
    escalation_required: Mapped[bool] = mapped_column(Boolean, default=False)
    answer_mode: Mapped[str] = mapped_column(String(10), index=True)  # live | demo | rule
    response_type: Mapped[str] = mapped_column(String(16))
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class SourceRecord(Base):
    __tablename__ = "source_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(255), index=True)
    chunk_id: Mapped[str] = mapped_column(String(300))
    score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)


class AdminRequest(Base):
    __tablename__ = "admin_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), index=True)
    request_type: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class EscalationEvent(Base):
    __tablename__ = "escalation_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # urgent | human_request
    reason: Mapped[str] = mapped_column(String(100))  # category only, no patient details
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    total: Mapped[int] = mapped_column(Integer)
    passed: Mapped[int] = mapped_column(Integer)
    metrics_json: Mapped[str] = mapped_column(Text)
    results: Mapped[List["EvaluationResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(40))
    passed: Mapped[bool] = mapped_column(Boolean)
    expected_intent: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    actual_intent: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float)
    detail: Mapped[str] = mapped_column(String(300), default="")
    run: Mapped[EvaluationRun] = relationship(back_populates="results")
