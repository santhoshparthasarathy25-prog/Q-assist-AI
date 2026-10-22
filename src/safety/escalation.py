"""Escalation messages and handoff helpers.

IMPORTANT: Emergency guidance below is GENERAL UK guidance. It is not a policy of the fictional clinic.
The prototype is not clinically validated and is not a triage tool."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

GENERAL_EMERGENCY_NOTE = "This is general UK emergency guidance, not a policy of the fictional demo clinic."

URGENT_MESSAGE = (
    "**This may be an emergency.** I'm an administrative assistant and cannot assess medical symptoms.\n\n"
    "- If someone's life may be at risk, **call 999 now**.\n"
    "- For urgent advice that is not life-threatening, contact **NHS 111** (online or by phone).\n"
    "- Do not wait for a reply from this chat.\n\n"
    f"_{GENERAL_EMERGENCY_NOTE}_  \n"
    "_A simulated alert has been recorded for the demo reception team; no real service has been contacted._"
)

HUMAN_HANDOFF_MESSAGE = (
    "Of course - I'll pass you to a member of the reception team. "
    "_(Simulated handoff: in this demo no real person or system has been contacted.)_ "
    "In the meantime you can use the clinic's contact details from the knowledge base page."
)

UNSUPPORTED_MEDICAL_MESSAGE = (
    "I'm sorry, I can't give medical advice, diagnoses or medication guidance. "
    "Please speak to a clinician - for example by requesting an appointment through the clinic, "
    "or contacting NHS 111 if it is urgent. If you think it is an emergency, call 999. "
    "I can help with opening hours, appointment and prescription processes, and general clinic information."
)

NO_VERIFIED_INFO_MESSAGE = (
    "I couldn't verify that from the available sample clinic documents, so I don't want to guess. "
    "I can pass your question to the reception team (simulated), or help with opening hours, "
    "appointment and prescription processes, and general clinic information."
)

INVALID_INPUT_MESSAGE = "Please type or speak a question (up to {limit} characters) and I'll do my best to help."

INJECTION_MESSAGE = "I can't help with that request. I can only answer questions about the demo clinic's administrative services."


@dataclass
class EscalationDecision:
    required: bool
    reason: Optional[str] = None  # category only - never the patient's full text
    kind: Optional[str] = None  # urgent | human_request


def urgent_decision(category: Optional[str]) -> EscalationDecision:
    return EscalationDecision(True, f"urgent_phrase:{category}", "urgent")


def human_decision() -> EscalationDecision:
    return EscalationDecision(True, "user_requested_human", "human_request")
