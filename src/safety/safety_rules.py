"""Deterministic safety rules. These run BEFORE any LLM call and are never delegated to a prompt.

Rules are plain regular expressions grouped by category so they are easy to read, extend and test.
Limitation: keyword rules cannot understand context (e.g. negation like "I do NOT have chest pain"
still triggers). The design deliberately prefers false alarms over missed emergencies."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

URGENT_PATTERNS = {
    "chest_pain": [r"\bchest (pain|tightness|pressure)\b", r"\bheart attack\b", r"\bpain in (my )?chest\b"],
    "breathing": [r"\b(can'?t|cannot|unable to|struggling to|difficulty|trouble) breath", r"\bshort(ness)? of breath\b",
                  r"\bnot breathing\b", r"\bstopped breathing\b", r"\bchoking\b"],
    "bleeding": [r"\bsevere(ly)? bleeding\b", r"\bbleeding (heavily|badly|a lot|won'?t stop)\b",
                 r"\bcan'?t stop (the )?bleeding\b", r"\bcoughing (up )?blood\b"],
    "stroke_signs": [r"\bstroke\b", r"\bface (is )?drooping\b", r"\bslurred speech\b", r"\bsudden(ly)? (weak|numb)"],
    "unconscious_seizure": [r"\bunconscious\b", r"\bunresponsive\b", r"\bpassed out\b", r"\bseizure\b",
                            r"\bfitting\b", r"\bcollapsed\b"],
    "overdose_poisoning": [r"\boverdos", r"\btook too many (pills|tablets)\b", r"\bpoison(ed|ing)\b"],
    "allergic_reaction": [r"\banaphyla", r"\bsevere allergic reaction\b", r"\bthroat (is )?(closing|swelling)\b",
                          r"\bswollen (tongue|throat)\b"],
    "self_harm": [r"\bkill myself\b", r"\bend my (own )?life\b", r"\bsuicid", r"\bwant to die\b",
                  r"\bhurt myself\b", r"\bself[- ]harm\b"],
}

# Clinical-advice requests are NOT emergencies, but the assistant must not answer them.
UNSUPPORTED_MEDICAL_PATTERNS = [
    r"\bwhat (dose|dosage)\b", r"\bhow (much|many) .{0,40}\b(should|can) i (take|use)\b",
    r"\bdiagnos", r"\bdo i have\b", r"\bwhat (is|could be) (wrong|causing)\b",
    r"\bis it safe to (take|mix|combine|drink)\b", r"\bwhat (medication|medicine|tablets?|drugs?) (should|can|do) i\b",
    r"\bshould i (stop|start|increase|reduce|take)\b", r"\b(side effects?|interact(s|ion)?) (of|with)\b",
    r"\bwhat (treatment|cure)\b", r"\bis (this|my|that) (rash|lump|mole|symptom)\b",
]

INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above) (instructions|rules|prompts?)",
    r"(reveal|show|print|repeat) (me )?(your|the) (system )?(prompt|instructions|api key|secrets?)",
    r"you are now\b", r"disregard (your|the) (rules|instructions)", r"\bjailbreak\b",
]

_URGENT_RE = {k: [re.compile(p, re.I) for p in v] for k, v in URGENT_PATTERNS.items()}
_MEDICAL_RE = [re.compile(p, re.I) for p in UNSUPPORTED_MEDICAL_PATTERNS]
_INJECTION_RE = [re.compile(p, re.I) for p in INJECTION_PATTERNS]


@dataclass
class SafetyResult:
    is_urgent: bool
    category: Optional[str] = None
    matched_rule: Optional[str] = None


def normalise(text: str) -> str:
    """Lower-case, collapse whitespace and unify apostrophes so rules match reliably."""
    return re.sub(r"\s+", " ", (text or "").replace("\u2019", "'")).strip().lower()


def check_urgent(text: str) -> SafetyResult:
    t = normalise(text)
    for category, regexes in _URGENT_RE.items():
        for rx in regexes:
            if rx.search(t):
                return SafetyResult(True, category, rx.pattern)
    return SafetyResult(False)


def is_unsupported_medical(text: str) -> bool:
    t = normalise(text)
    return any(rx.search(t) for rx in _MEDICAL_RE)


def looks_like_injection(text: str) -> bool:
    t = normalise(text)
    return any(rx.search(t) for rx in _INJECTION_RE)
