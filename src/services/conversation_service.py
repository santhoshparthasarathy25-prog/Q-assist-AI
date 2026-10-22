"""Conversation/session management.

Isolation model: every browser session gets its own random session_id and conversation id (kept in
Streamlit session_state). History is read ONLY by conversation id, so one session never sees
another's messages. This is NOT authentication - see docs/safety_and_limitations.md."""
from __future__ import annotations

import uuid
from typing import List, Tuple


class ConversationService:
    def __init__(self, repo):
        self.repo = repo

    def start(self, session_id: str | None = None, is_seed: bool = False) -> int:
        return self.repo.create_conversation(session_id or uuid.uuid4().hex, is_seed)

    def history(self, conversation_id: int, limit: int = 12) -> List[Tuple[str, str]]:
        return self.repo.get_history(conversation_id, limit)

    def clear(self, conversation_id: int, session_id: str) -> int:
        """End the current conversation and start a fresh one (old messages are no longer used as context)."""
        self.repo.end_conversation(conversation_id)
        return self.start(session_id)
