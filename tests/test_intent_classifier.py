from src.nlp.intent_classifier import classify_intent

CASES = [
    ("How do I book an appointment?", "appointment_info"),
    ("I need to cancel my appointment", "appointment_info"),
    ("How do I get a repeat prescription?", "prescription_info"),
    ("When are you open on Saturday?", "opening_hours"),
    ("Do you have wheelchair access?", "general_info"),
    ("I want to update my address", "admin_request"),
    ("Can I speak to a human please", "human_assistance"),
    ("I have chest pain", "urgent"),
    ("What dose of ibuprofen should I take", "unsupported"),
    ("Tell me a joke", "unknown"),
]


def test_labelled_examples():
    for text, expected in CASES:
        assert classify_intent(text).label == expected, text


def test_result_structure():
    r = classify_intent("How do I book an appointment?")
    assert r.workflow == "appointment_enquiry_log"
    assert r.rule_matches >= 1 and r.reason and "not a calibrated probability" in r.confidence_note
    assert r.escalation_required is False


def test_escalation_flags():
    assert classify_intent("I have chest pain").escalation_required
    assert classify_intent("connect me to a person").escalation_required
    assert not classify_intent("What are your opening hours?").escalation_required


def test_empty_and_unknown():
    assert classify_intent("").label == "unknown"
    assert classify_intent("   ").label == "unknown"
    assert classify_intent("What is the capital of France?").label == "unknown"


def test_urgent_has_priority_over_other_intents():
    assert classify_intent("I need an appointment, I have severe chest pain").label == "urgent"
