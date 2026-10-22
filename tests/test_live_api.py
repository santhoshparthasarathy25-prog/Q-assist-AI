"""Optional live test - skipped unless GEMINI_API_KEY is set AND RUN_LIVE_TESTS=1. Never runs in normal CI."""
import os

import pytest

from config.settings import get_settings
from src.llm.llm_service import LLMService

pytestmark = pytest.mark.skipif(not (os.getenv("GEMINI_API_KEY") and os.getenv("RUN_LIVE_TESTS") == "1"),
                                reason="live API test disabled")


def test_live_round_trip():
    r = LLMService(get_settings()).generate("Reply with the single word OK.", "ping")
    assert r.mode == "live" and r.text
