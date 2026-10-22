"""Reusable LLM service (Google Gen AI SDK / Gemini).

Never raises to the UI: generate() always returns an LLMResult whose `mode` is honest:
  'live'  -> text really came from the model
  'demo'  -> no live call was made / possible (reason in `error`)"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from config.settings import Settings, get_settings
from src.utils.exceptions import LLMUnavailableError

log = logging.getLogger(__name__)

FRIENDLY = {
    "no_key": "No GEMINI_API_KEY configured - running in demo mode.",
    "invalid_credentials": "The Gemini API key was rejected. Check GEMINI_API_KEY.",
    "rate_limit": "Gemini rate limit reached. Try again shortly.",
    "timeout": "The Gemini request timed out.",
    "network": "Could not reach the Gemini service (network problem).",
    "malformed": "The model returned an empty or malformed response.",
    "other": "The Gemini service returned an error.",
}


@dataclass
class LLMResult:
    text: str
    mode: str  # live | demo
    error: Optional[str] = None
    error_kind: Optional[str] = None
    model: Optional[str] = None


def classify_exception(exc: Exception) -> str:
    """Map an SDK/network exception to one of our error kinds without depending on SDK internals."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if code in (401, 403) or "api key" in msg and ("invalid" in msg or "not valid" in msg):
        return "invalid_credentials"
    if code == 429 or "quota" in msg or "rate" in msg and "limit" in msg or "resource_exhausted" in msg:
        return "rate_limit"
    if "timeout" in name or "timed out" in msg or "deadline" in msg or code == 504:
        return "timeout"
    if any(w in name for w in ("connect", "network", "dns")) or "connection" in msg or "name resolution" in msg:
        return "network"
    return "other"


class LLMService:
    def __init__(self, settings: Settings | None = None, client=None):
        self.s = settings or get_settings()
        self._client = client  # injectable for tests

    @property
    def available(self) -> bool:
        return self.s.llm_configured or self._client is not None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.s.llm_configured:
            raise LLMUnavailableError(FRIENDLY["no_key"], "no_key")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise LLMUnavailableError("google-genai is not installed (pip install google-genai).", "other") from exc
        self._client = genai.Client(
            api_key=self.s.gemini_api_key,
            http_options=types.HttpOptions(timeout=int(self.s.llm_timeout_seconds * 1000)),
        )
        return self._client

    def _call(self, system: str, user: str) -> str:
        client = self._get_client()
        try:
            from google.genai import types
            config = types.GenerateContentConfig(system_instruction=system, temperature=0.2, max_output_tokens=400)
            resp = client.models.generate_content(model=self.s.gemini_model, contents=user, config=config)
        except LLMUnavailableError:
            raise
        except ImportError:  # injected client without SDK installed (tests)
            resp = client.models.generate_content(model=self.s.gemini_model, contents=user,
                                                  config={"system_instruction": system})
        text = getattr(resp, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise LLMUnavailableError(FRIENDLY["malformed"], "malformed")
        return text.strip()

    def generate(self, system: str, user: str) -> LLMResult:
        try:
            text = self._call(system, user)
            return LLMResult(text, "live", model=self.s.gemini_model)
        except LLMUnavailableError as exc:
            return LLMResult("", "demo", FRIENDLY.get(exc.kind, str(exc)), exc.kind)
        except Exception as exc:  # noqa: BLE001 - convert every SDK/network failure
            kind = classify_exception(exc)
            log.warning("LLM call failed (%s: %s)", type(exc).__name__, kind)  # no prompt content logged
            return LLMResult("", "demo", FRIENDLY[kind], kind)
