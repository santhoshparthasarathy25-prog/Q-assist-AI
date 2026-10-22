"""Simulated administrative workflows. NOTHING here contacts a real system."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.nlp.intent_classifier import IntentResult

SIM_NOTE = "Simulated workflow - no real appointment, prescription, message or external system was involved."


@dataclass
class WorkflowOutcome:
    request_type: Optional[str]  # None = nothing to log
    status: str
    simulated: bool
    description: str


# intent -> (request_type, status when answered, description)
_MAP = {
    "appointment_info": ("appointment_enquiry", "logged_simulated", "Appointment enquiry logged (simulated)"),
    "prescription_info": ("prescription_enquiry", "logged_simulated", "Prescription enquiry logged (simulated)"),
    "opening_hours": ("general_information", "answered", "General information request answered"),
    "general_info": ("general_information", "answered", "General information request answered"),
    "admin_request": ("admin_request", "logged_simulated", "Administrative request logged (simulated)"),
    "human_assistance": ("human_assistance", "handoff_simulated", "Human assistance request queued (simulated)"),
    "urgent": ("escalation", "escalated_simulated", "Urgent-risk escalation recorded (simulated)"),
    "unsupported": ("out_of_scope", "declined_out_of_scope", "Medical-advice request declined; redirected"),
    "unknown": ("unverified_question", "no_verified_answer", "No verified answer; offered handoff (simulated)"),
}


def route_request(intent: IntentResult, answered_from_kb: bool = True) -> WorkflowOutcome:
    """Pick the simulated workflow. If an info intent found no reliable source, mark it unverified."""
    rtype, status, desc = _MAP.get(intent.label, _MAP["unknown"])
    if intent.label in ("opening_hours", "general_info") and not answered_from_kb:
        rtype, status, desc = _MAP["unknown"]
    return WorkflowOutcome(rtype, status, True, desc + ". " + SIM_NOTE)
