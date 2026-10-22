from config.settings import get_settings
from src.llm.llm_service import LLMService, classify_exception
import dataclasses


def _svc(client=None, key=""):
    return LLMService(dataclasses.replace(get_settings(), gemini_api_key=key), client=client)


class _Raises:
    def __init__(self, exc):
        self.exc = exc
        outer = self

        class models:
            @staticmethod
            def generate_content(**_):
                raise outer.exc
        self.models = models


class _Returns:
    def __init__(self, text):
        class R:
            pass
        r = R(); r.text = text
        class models:
            @staticmethod
            def generate_content(**_):
                return r
        self.models = models


class _CodeErr(Exception):
    def __init__(self, code, msg=""):
        super().__init__(msg); self.code = code


def test_no_key_means_demo_mode_without_exception():
    r = _svc().generate("sys", "user")
    assert r.mode == "demo" and r.error_kind == "no_key" and r.text == ""


def test_live_response_is_labelled_live():
    r = _svc(client=_Returns("Hello")).generate("s", "u")
    assert r.mode == "live" and r.text == "Hello"


def test_failure_modes_map_to_demo_with_kind():
    assert _svc(client=_Raises(_CodeErr(429))).generate("s", "u").error_kind == "rate_limit"
    assert _svc(client=_Raises(_CodeErr(403))).generate("s", "u").error_kind == "invalid_credentials"
    assert _svc(client=_Raises(TimeoutError("timed out"))).generate("s", "u").error_kind == "timeout"
    assert _svc(client=_Raises(ConnectionError("down"))).generate("s", "u").error_kind == "network"
    assert _svc(client=_Raises(ValueError("boom"))).generate("s", "u").mode == "demo"


def test_malformed_response():
    for bad in ("", "   ", None):
        r = _svc(client=_Returns(bad)).generate("s", "u")
        assert r.mode == "demo" and r.error_kind == "malformed"


def test_classify_exception():
    assert classify_exception(_CodeErr(401)) == "invalid_credentials"
    assert classify_exception(RuntimeError("something else")) == "other"
