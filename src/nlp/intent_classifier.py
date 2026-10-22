"""Rule-based intent classifier.

How it works (easy to explain in an interview):
1. Urgent-risk rules are checked first (safety always wins).
2. Then requests for a human, then requests for medical advice (unsupported).
3. Otherwise each remaining intent has a list of regex 'rules'. We count how many distinct rules
   match. The intent with the most matches wins; ties are broken by a fixed priority order.
4. No match -> 'unknown'.

`rule_matches` is a COUNT of matched rules. It is NOT a probability and is not statistically calibrated."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from src.safety.safety_rules import check_urgent, is_unsupported_medical, normalise

INTENTS = ["appointment_info", "prescription_info", "opening_hours", "general_info",
           "admin_request", "human_assistance", "urgent", "unsupported", "unknown"]

WORKFLOWS = {
    "appointment_info": "appointment_enquiry_log",
    "prescription_info": "prescription_enquiry_log",
    "opening_hours": "general_information",
    "general_info": "general_information",
    "admin_request": "admin_request_log",
    "human_assistance": "human_handoff",
    "urgent": "urgent_escalation",
    "unsupported": "safe_decline",
    "unknown": "fallback_no_verified_info",
}

RULES: Dict[str, List[str]] = {
    "human_assistance": [
        r"\b(speak|talk|chat) (to|with) (a |an |the )?(human|person|someone|somebody|receptionist|member of staff|staff|agent|real person)\b",
        r"\b(human|real person|receptionist) (please|help)\b", r"\bconnect me\b", r"\btransfer me\b",
        r"\bnot a (robot|bot)\b", r"\bcall me back\b", r"\bhuman assistance\b",
    ],
    "prescription_info": [
        r"\bprescription", r"\brepeat (medication|medicine|script)", r"\brefill\b", r"\bpharmacy\b",
        r"\border (my )?(medication|medicine|tablets)\b", r"\brun(ning)? out of (my )?(medication|medicine|tablets)\b",
    ],
    "appointment_info": [
        r"\bappointment", r"\bbook(ing)?\b", r"\breschedul", r"\bcancel (my|an|the)\b",
        r"\bsee (a|the) (gp|doctor|nurse)\b", r"\bsame[- ]day\b", r"\bseen by\b", r"\bsee a clinician\b",
    ],
    "opening_hours": [
        r"\bopening (hours|times)\b", r"\bopen (on|at|today|tomorrow|late|now|until)\b", r"\bwhen (are|do) you (open|close)\b",
        r"\bclos(e|ed|ing)( time)?\b", r"\bbank holiday", r"\bwhat time\b", r"\bhours of\b", r"\b(saturday|sunday|weekend)s?\b",
    ],
    "admin_request": [
        r"\b(update|change|amend|correct) (my )?(details|address|phone|number|name|email|contact)\b",
        r"\bregister\b", r"\bfit note\b", r"\bsick note\b", r"\b(medical )?records?\b", r"\bcomplain", r"\bletter\b",
        r"\bsubmit (a |an )?(form|request)\b", r"\bleave a message\b", r"\bsend a message\b", r"\bregistration\b",
    ],
    "general_info": [
        r"\bwheelchair\b", r"\baccessib", r"\bparking\b", r"\bcontact (details|number|us)\b", r"\bphone number\b",
        r"\baddress\b", r"\bwhere (is|are) (the |your )?(clinic|surgery)\b", r"\binterpreter\b", r"\bhearing loop\b",
        r"\bpolicy\b", r"\bpolicies\b", r"\bemail\b", r"\bfacilit", r"\bdisabled\b", r"\bbsl\b", r"\blanguage\b",
    ],
}
PRIORITY = ["prescription_info", "appointment_info", "opening_hours", "admin_request", "general_info"]
_COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in RULES.items()}


@dataclass
class IntentResult:
    label: str
    rule_matches: int
    reason: str
    workflow: str
    escalation_required: bool
    matched_rules: List[str] = field(default_factory=list)
    confidence_note: str = "Rule-match count (not a calibrated probability)"


def classify_intent(text: str) -> IntentResult:
    t = normalise(text)
    if not t:
        return IntentResult("unknown", 0, "Empty input", WORKFLOWS["unknown"], False)

    urgent = check_urgent(t)
    if urgent.is_urgent:
        return IntentResult("urgent", 1, f"Urgent-risk rule matched (category: {urgent.category})",
                            WORKFLOWS["urgent"], True, [urgent.matched_rule or ""])

    human = [rx.pattern for rx in _COMPILED["human_assistance"] if rx.search(t)]
    if human:
        return IntentResult("human_assistance", len(human), "User asked to speak to a person",
                            WORKFLOWS["human_assistance"], True, human)

    if is_unsupported_medical(t):
        return IntentResult("unsupported", 1, "Request for medical advice/diagnosis is outside scope",
                            WORKFLOWS["unsupported"], False)

    hits: Dict[str, List[str]] = {}
    for label in PRIORITY:
        m = [rx.pattern for rx in _COMPILED[label] if rx.search(t)]
        if m:
            hits[label] = m
    if not hits:
        return IntentResult("unknown", 0, "No intent rule matched", WORKFLOWS["unknown"], False)

    best = max(hits, key=lambda k: (len(hits[k]), -PRIORITY.index(k)))
    return IntentResult(best, len(hits[best]), f"{len(hits[best])} rule(s) matched for '{best}'",
                        WORKFLOWS[best], False, hits[best])
