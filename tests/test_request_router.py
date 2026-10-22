from src.nlp.intent_classifier import classify_intent
from src.workflows.request_router import route_request


def test_appointment_is_simulated_and_not_booked():
    out = route_request(classify_intent("How do I book an appointment?"))
    assert out.request_type == "appointment_enquiry" and out.simulated
    assert out.status == "logged_simulated" and "Simulated workflow" in out.description


def test_prescription_and_admin():
    assert route_request(classify_intent("repeat prescription")).request_type == "prescription_enquiry"
    assert route_request(classify_intent("update my address")).request_type == "admin_request"


def test_human_and_urgent():
    assert route_request(classify_intent("speak to a person")).status == "handoff_simulated"
    assert route_request(classify_intent("severe chest pain")).status == "escalated_simulated"


def test_unverified_when_no_source():
    out = route_request(classify_intent("Do you have wheelchair access?"), answered_from_kb=False)
    assert out.status == "no_verified_answer"


def test_unsupported_medical_declined():
    assert route_request(classify_intent("what dose of aspirin should I take")).status == "declined_out_of_scope"
